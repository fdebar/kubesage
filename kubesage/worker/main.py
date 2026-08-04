from kubesage.bootstrap import create_analysis_service
from kubesage.database.session import SessionLocal
from kubesage.watchers.kubernetes_event_source import KubernetesEventSource
from kubesage.watchers.kubernetes_watcher import KubernetesWatcher
from kubesage.watchers.pod_event_filter import PodEventFilter


def main() -> None:
    db = SessionLocal()
    try:
        analysis_service = create_analysis_service(db)
        watcher = KubernetesWatcher(
            analysis_service=analysis_service,
            event_filter=PodEventFilter(),
        )
        event_source = KubernetesEventSource()

        watcher.start(event_source)
    finally:
        db.close()


if __name__ == "__main__":
    main()
