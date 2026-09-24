from __future__ import annotations

import time
from collections import deque
from queue import Empty, Queue
from threading import BoundedSemaphore, Thread

import structlog

from kubesage.bootstrap import create_analysis_service
from kubesage.database.session import SessionLocal
from kubesage.models.analysis import AnalysisTrigger
from kubesage.observability.metrics import WATCHER_QUEUE_DEPTH
from kubesage.utils.config import settings
from kubesage.utils.exceptions import PodIdentityMismatchError, PodNotFoundError
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.models.incident_trigger import IncidentTrigger

logger = structlog.get_logger()


class AnalysisWorker:
    """
    Consumes incident triggers independently from the Kubernetes watch.
    """

    def __init__(
        self,
        deduplicator: IncidentDeduplicator,
        queue_size: int = settings.worker_queue_size,
        max_retries: int = settings.worker_analysis_retries,
    ) -> None:
        self.deduplicator = deduplicator
        self.max_retries = max(1, max_retries)
        self._capacity = BoundedSemaphore(max(1, queue_size))
        self._queue: Queue[IncidentTrigger] = Queue(maxsize=max(1, queue_size))
        self._thread = Thread(
            target=self._run,
            name="kubesage-analysis-worker",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

        logger.info(
            "analysis_worker_started",
            queue_size=self._queue.maxsize,
            max_retries=self.max_retries,
        )

    def submit(self, trigger: IncidentTrigger) -> None:
        """
        Blocks when the queue is full.

        This intentionally provides backpressure instead of silently
        dropping incident triggers.
        """

        self._capacity.acquire()
        try:
            self._queue.put(trigger)
        except Exception:
            self._capacity.release()
            raise

        WATCHER_QUEUE_DEPTH.set(self._queue.qsize())

    def _run(self) -> None:
        pending_retries: deque[IncidentTrigger] = deque()
        process_retry_next = False

        while True:
            from_queue = False

            if pending_retries and process_retry_next:
                trigger = pending_retries.popleft()
            else:
                try:
                    trigger = self._queue.get(timeout=0.1)
                    from_queue = True
                except Empty:
                    if not pending_retries:
                        continue
                    trigger = pending_retries.popleft()

            try:
                completed = self._process(trigger)
                if completed:
                    self._capacity.release()
                else:
                    pending_retries.append(trigger)
            finally:
                if from_queue:
                    self._queue.task_done()

                WATCHER_QUEUE_DEPTH.set(self._queue.qsize() + len(pending_retries))

            # Give queued new incidents and failed incidents turns in rotation.
            process_retry_next = from_queue

    def _process(self, trigger: IncidentTrigger) -> bool:
        for attempt in range(1, self.max_retries + 1):
            db = None

            try:
                db = SessionLocal()
                analysis_service = create_analysis_service(db)

                analysis_service.analyze(
                    trigger.namespace,
                    trigger.pod,
                    AnalysisTrigger.WATCHER,
                    trigger.pod_uid,
                )

                logger.info(
                    "worker_analysis_completed",
                    namespace=trigger.namespace,
                    pod=trigger.pod,
                    pod_uid=trigger.pod_uid,
                    resource_version=trigger.resource_version,
                    reason=trigger.reason,
                )

                return True

            except PodIdentityMismatchError:
                logger.info(
                    "worker_analysis_stale_pod_skipped",
                    namespace=trigger.namespace,
                    pod=trigger.pod,
                    expected_pod_uid=trigger.pod_uid,
                )

                return True

            except PodNotFoundError:
                logger.info(
                    "worker_analysis_pod_not_found",
                    namespace=trigger.namespace,
                    pod=trigger.pod,
                    pod_uid=trigger.pod_uid,
                )

                # Terminal result: do not retry a Pod which has already disappeared.
                return True

            except Exception:
                if attempt == self.max_retries:
                    logger.exception(
                        "worker_analysis_requeued_after_failures",
                        namespace=trigger.namespace,
                        pod=trigger.pod,
                        pod_uid=trigger.pod_uid,
                        resource_version=trigger.resource_version,
                        reason=trigger.reason,
                        attempts=attempt,
                    )
                    return False
                else:
                    logger.exception(
                        "worker_analysis_retrying",
                        namespace=trigger.namespace,
                        pod=trigger.pod,
                        pod_uid=trigger.pod_uid,
                        attempt=attempt,
                        max_retries=self.max_retries,
                    )

                    time.sleep(min(2 ** min(attempt - 1, 6), 60))

            finally:
                if db is not None:
                    try:
                        db.close()
                    except Exception:
                        logger.exception(
                            "worker_database_session_close_failed",
                            namespace=trigger.namespace,
                            pod=trigger.pod,
                            attempt=attempt,
                        )

        return False
