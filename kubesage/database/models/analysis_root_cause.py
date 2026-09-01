from uuid import uuid4

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class AnalysisRootCauseModel(Base):
    __tablename__ = "analysis_root_causes"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("analyses.id"),
        nullable=False,
        index=True,
    )
    finding: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    supporting_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    supporting_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis = relationship(
        "AnalysisModel",
        back_populates="root_causes",
    )
