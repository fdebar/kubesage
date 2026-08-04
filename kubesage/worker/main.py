import structlog

from kubesage.bootstrap import create_analysis_service
from kubesage.database.session import SessionLocal
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.kubernetes_event_source import (
    KubernetesPodEventSource,
)
from kubesage.watchers.kubernetes_watcher import KubernetesWatcher
from kubesage.watchers.pod_event_filter import PodEventFilter

logger = structlog.get_logger()


def run_worker() -> None:
    db = SessionLocal()
    try:
        analysis_service = create_analysis_service(db)
        watcher = KubernetesWatcher(
            analysis_service=analysis_service,
            event_filter=PodEventFilter(),
            deduplicator=IncidentDeduplicator(),
        )
        event_source = KubernetesPodEventSource()
        logger.info("kubesage_worker_started")
        watcher.start(event_source)
    except Exception:
        logger.exception("kubesage_worker_failed")
        raise

    finally:
        db.close()


def main() -> None:
    run_worker()


if __name__ == "__main__":
    main()
