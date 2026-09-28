from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from kubesage.database.models.incident_deduplication import (
    IncidentDeduplicationModel,
)
from kubesage.watchers.models.incident_trigger import IncidentTrigger

SessionFactory = Callable[[], Session]


class IncidentDeduplicationRepository:
    """Stores watcher deduplication keys with an expiring database TTL."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self.session_factory = session_factory

    def claim(self, trigger: IncidentTrigger, ttl: timedelta) -> bool:
        now = datetime.now(UTC)

        with self.session_factory() as session:
            session.execute(
                delete(IncidentDeduplicationModel).where(
                    IncidentDeduplicationModel.expires_at <= now
                )
            )
            session.add(
                IncidentDeduplicationModel(
                    namespace=trigger.namespace,
                    pod_uid=trigger.pod_uid,
                    reason=trigger.reason,
                    seen_at=now,
                    expires_at=now + ttl,
                )
            )
            try:
                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                return False

    def forget(self, trigger: IncidentTrigger) -> None:
        with self.session_factory() as session:
            session.execute(
                delete(IncidentDeduplicationModel).where(
                    IncidentDeduplicationModel.namespace == trigger.namespace,
                    IncidentDeduplicationModel.pod_uid == trigger.pod_uid,
                    IncidentDeduplicationModel.reason == trigger.reason,
                )
            )
            session.commit()
