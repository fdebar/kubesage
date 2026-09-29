from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from kubesage.database.base import Base


class WatcherIncidentModel(Base):
    __tablename__ = "watcher_incidents"
    __table_args__ = (
        Index("ix_watcher_incidents_status", "status"),
        Index(
            "ix_watcher_incidents_pod_reason_status",
            "namespace",
            "pod_uid",
            "reason",
            "status",
        ),
    )

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    namespace: Mapped[str] = mapped_column(String(255), nullable=False)
    pod_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    pod: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_resource_version: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str | None] = mapped_column(nullable=True)
