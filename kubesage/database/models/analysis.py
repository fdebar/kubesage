from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class AnalysisModel(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    namespace: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pod: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    highest_severity: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    findings = relationship(
        "FindingModel",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )

    report = relationship(
        "AIReportModel",
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan",
    )
