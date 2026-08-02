from uuid import uuid4

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class AIReportModel(Base):
    __tablename__ = "ai_reports"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("analyses.id"), nullable=False, unique=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis = relationship("AnalysisModel", back_populates="report")
