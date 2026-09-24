import structlog

from kubesage.bootstrap import check_application_requirements
from kubesage.observability.worker_metrics import start_metrics_server
from kubesage.utils.config import settings
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.kubernetes_event_source import (
    KubernetesPodEventSource,
)
from kubesage.watchers.kubernetes_watcher import KubernetesWatcher
from kubesage.watchers.pod_event_filter import PodEventFilter
from kubesage.watchers.pod_state_cache import PodStateCache
from kubesage.watchers.pod_state_diff_builder import PodStateDiffBuilder
from kubesage.worker.analysis_worker import AnalysisWorker

logger = structlog.get_logger()


def run_worker() -> None:
    check_application_requirements()
    start_metrics_server(settings.metrics_port)

    deduplicator = IncidentDeduplicator()

    analysis_worker = AnalysisWorker(
        deduplicator=deduplicator,
        queue_size=settings.worker_queue_size,
        max_retries=settings.worker_analysis_retries,
    )

    analysis_worker.start()

    watcher = KubernetesWatcher(
        event_filter=PodEventFilter(),
        deduplicator=deduplicator,
        state_cache=PodStateCache(),
        diff_builder=PodStateDiffBuilder(),
        analysis_submitter=analysis_worker.submit,
    )

    logger.info("kubesage_worker_started")

    watcher.start(KubernetesPodEventSource())


def main() -> None:
    run_worker()


if __name__ == "__main__":
    main()
