from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class AnalysisModel(Base):
    __tablename__ = "analyses"

    __table_args__ = (
        Index("ix_analysis_created_at", "created_at"),
        Index("ix_analysis_namespace", "namespace"),
        Index("ix_analysis_highest_severity", "highest_severity"),
    )

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    namespace: Mapped[str] = mapped_column(String(255), nullable=False)
    pod: Mapped[str] = mapped_column(String(255), nullable=False)
    pod_uid: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    trigger: Mapped[str] = mapped_column(String(25), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    highest_severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    findings_count: Mapped[int] = mapped_column(Integer, nullable=False)
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
    incident_snapshot = relationship(
        "IncidentSnapshotModel",
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan",
    )
    correlations = relationship(
        "AnalysisCorrelationModel",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    root_causes = relationship(
        "AnalysisRootCauseModel",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
