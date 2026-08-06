import structlog
from prometheus_client import start_http_server

from kubesage.bootstrap import create_analysis_service
from kubesage.database.session import SessionLocal
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
    _start_prometheus_server()
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


def _start_prometheus_server() -> None:
    """
    Starts the Prometheus metrics server on port ${settings.metrics_port}.
    Metrics must be exposed for monitoring and alerting purposes.

    Raises:
        Exception: If the Prometheus metrics server fails to start.
    """

    try:
        start_http_server(settings.metrics_port)
        logger.info("prometheus_server_started", port=settings.metrics_port)
    except Exception:
        logger.exception("prometheus_server_start_failed")
        raise


if __name__ == "__main__":
    main()
