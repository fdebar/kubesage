from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from kubesage.database.base import Base


class IncidentDeduplicationModel(Base):
    __tablename__ = "incident_deduplication"
    __table_args__ = (Index("ix_incident_deduplication_expires_at", "expires_at"),)

    namespace: Mapped[str] = mapped_column(String(255), primary_key=True)
    pod_uid: Mapped[str] = mapped_column(String(255), primary_key=True)
    reason: Mapped[str] = mapped_column(String(100), primary_key=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
