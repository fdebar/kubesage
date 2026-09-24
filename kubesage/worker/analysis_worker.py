from __future__ import annotations

import time
from queue import Queue
from threading import Thread

import structlog

from kubesage.bootstrap import create_analysis_service
from kubesage.database.session import SessionLocal
from kubesage.models.analysis import AnalysisTrigger
from kubesage.observability.metrics import WATCHER_QUEUE_DEPTH
from kubesage.utils.config import settings
from kubesage.utils.exceptions import PodNotFoundError
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
        self._queue: Queue[IncidentTrigger] = Queue(maxsize=queue_size)
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

        self._queue.put(trigger)

        WATCHER_QUEUE_DEPTH.set(self._queue.qsize())

    def _run(self) -> None:
        while True:
            trigger = self._queue.get()

            try:
                self._process(trigger)
            finally:
                self._queue.task_done()

                WATCHER_QUEUE_DEPTH.set(self._queue.qsize())

    def _process(self, trigger: IncidentTrigger) -> None:
        attempt = 0

        while True:
            attempt += 1
            db = None

            try:
                db = SessionLocal()
                analysis_service = create_analysis_service(db)

                analysis_service.analyze(
                    trigger.namespace,
                    trigger.pod,
                    AnalysisTrigger.WATCHER,
                )

                logger.info(
                    "worker_analysis_completed",
                    namespace=trigger.namespace,
                    pod=trigger.pod,
                    pod_uid=trigger.pod_uid,
                    resource_version=trigger.resource_version,
                    reason=trigger.reason,
                )

                return

            except PodNotFoundError:
                logger.info(
                    "worker_analysis_pod_not_found",
                    namespace=trigger.namespace,
                    pod=trigger.pod,
                    pod_uid=trigger.pod_uid,
                )

                # Terminal result: do not retry a Pod which has already disappeared.
                return

            except Exception:
                if attempt % self.max_retries == 0:
                    logger.exception(
                        "worker_analysis_still_failing",
                        namespace=trigger.namespace,
                        pod=trigger.pod,
                        pod_uid=trigger.pod_uid,
                        resource_version=trigger.resource_version,
                        reason=trigger.reason,
                        attempts=attempt,
                    )
                else:
                    logger.exception(
                        "worker_analysis_retrying",
                        namespace=trigger.namespace,
                        pod=trigger.pod,
                        pod_uid=trigger.pod_uid,
                        attempt=attempt,
                        max_retries=self.max_retries,
                    )

                # The watch cursor may already have advanced beyond this
                # trigger, so retain it here instead of relying on Kubernetes
                # to replay the event after the retry budget is exhausted.
                time.sleep(min(2 ** min(attempt - 1, 6), 60))

            finally:
                if db is not None:
                    db.close()
