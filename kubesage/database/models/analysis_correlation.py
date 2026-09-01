from uuid import uuid4

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class AnalysisCorrelationModel(Base):
    __tablename__ = "analysis_correlations"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("analyses.id"), nullable=False, index=True
    )
    source_finding: Mapped[str] = mapped_column(String(255), nullable=False)
    target_finding: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis = relationship(
        "AnalysisModel",
        back_populates="correlations",
    )
