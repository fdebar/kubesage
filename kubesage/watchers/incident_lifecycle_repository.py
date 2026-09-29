from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from typing import Any

from kubernetes.client import V1Pod
from sqlalchemy import select
from sqlalchemy.orm import Session

from kubesage.database.models.watcher_incident import WatcherIncidentModel

SessionFactory = Callable[[], Session]


class WatcherIncidentLifecycleRepository:
    """Persists open watcher incidents and records their recovery."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self.session_factory = session_factory

    def sync_pod(
        self,
        pod: V1Pod,
        current_reason: str | None,
        current_message: str | None = None,
    ) -> None:
        metadata = pod.metadata
        if metadata is None or metadata.namespace is None or metadata.uid is None:
            return

        now = datetime.now(UTC)
        with self.session_factory() as session:
            if current_reason is not None:
                row = self._find_active(
                    session,
                    metadata.namespace,
                    metadata.uid,
                    current_reason,
                )
                if row is None:
                    row = WatcherIncidentModel(
                        namespace=metadata.namespace,
                        pod_uid=metadata.uid,
                        reason=current_reason,
                        pod=metadata.name or "unknown",
                        status="active",
                        first_seen_at=now,
                        last_seen_at=now,
                        last_resource_version=metadata.resource_version,
                        message=current_message,
                    )
                    session.add(row)
                else:
                    row.status = "active"
                    row.last_seen_at = now
                    row.resolved_at = None
                    row.pod = metadata.name or row.pod
                    row.last_resource_version = metadata.resource_version
                    row.message = current_message

            self._resolve_other_reasons(
                session,
                metadata.namespace,
                metadata.uid,
                current_reason,
                now,
            )
            session.commit()

    def resolve_pod(self, namespace: str, pod_uid: str) -> None:
        now = datetime.now(UTC)
        with self.session_factory() as session:
            rows = (
                session.execute(
                    select(WatcherIncidentModel).where(
                        WatcherIncidentModel.namespace == namespace,
                        WatcherIncidentModel.pod_uid == pod_uid,
                        WatcherIncidentModel.status == "active",
                    )
                )
                .scalars()
                .all()
            )
            for row in rows:
                row.status = "resolved"
                row.resolved_at = now
            session.commit()

    @staticmethod
    def _find_active(
        session: Session,
        namespace: str,
        pod_uid: str,
        reason: str,
    ) -> Any | None:
        return (
            session.execute(
                select(WatcherIncidentModel).where(
                    WatcherIncidentModel.namespace == namespace,
                    WatcherIncidentModel.pod_uid == pod_uid,
                    WatcherIncidentModel.reason == reason,
                    WatcherIncidentModel.status == "active",
                )
            )
            .scalars()
            .first()
        )

    def resolve_missing_pods(self, pods: Iterable[V1Pod]) -> None:
        present = {
            (pod.metadata.namespace, pod.metadata.uid)
            for pod in pods
            if pod.metadata is not None
            and pod.metadata.namespace is not None
            and pod.metadata.uid is not None
        }
        now = datetime.now(UTC)
        with self.session_factory() as session:
            rows = (
                session.execute(
                    select(WatcherIncidentModel).where(
                        WatcherIncidentModel.status == "active"
                    )
                )
                .scalars()
                .all()
            )
            for row in rows:
                if (row.namespace, row.pod_uid) not in present:
                    row.status = "resolved"
                    row.resolved_at = now
            session.commit()

    @staticmethod
    def _resolve_other_reasons(
        session: Session,
        namespace: str,
        pod_uid: str,
        current_reason: str | None,
        now: datetime,
    ) -> None:
        rows = (
            session.execute(
                select(WatcherIncidentModel).where(
                    WatcherIncidentModel.namespace == namespace,
                    WatcherIncidentModel.pod_uid == pod_uid,
                    WatcherIncidentModel.status == "active",
                )
            )
            .scalars()
            .all()
        )
        for row in rows:
            if row.reason != current_reason:
                row.status = "resolved"
                row.resolved_at = now
