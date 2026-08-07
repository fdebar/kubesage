from uuid import uuid4

from sqlalchemy import JSON, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class AIReportModel(Base):
    __tablename__ = "ai_reports"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("analyses.id"),
        nullable=False,
        unique=True,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_investigations: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    analysis = relationship("AnalysisModel", back_populates="report")
