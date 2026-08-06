import structlog

from kubesage.bootstrap import create_analysis_service
from kubesage.database.session import SessionLocal
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

logger = structlog.get_logger()


def run_worker() -> None:
    start_metrics_server(settings.metrics_port)
    db = SessionLocal()

    try:
        watcher = KubernetesWatcher(
            analysis_service=create_analysis_service(db),
            event_filter=PodEventFilter(),
            deduplicator=IncidentDeduplicator(),
            state_cache=PodStateCache(),
            diff_builder=PodStateDiffBuilder(),
        )
        logger.info("kubesage_worker_started")
        watcher.start(KubernetesPodEventSource())
    except Exception:
        logger.exception("kubesage_worker_failed")
        raise

    finally:
        db.close()


def main() -> None:
    run_worker()


if __name__ == "__main__":
    main()
