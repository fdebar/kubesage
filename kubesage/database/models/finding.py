from uuid import uuid4

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class FindingModel(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), nullable=False)
    rule: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resource_api_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_kind: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_namespace: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidences = relationship(
        "EvidenceModel", back_populates="finding", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "RecommendationModel", back_populates="finding", cascade="all, delete-orphan"
    )
    analysis = relationship("AnalysisModel", back_populates="findings")
