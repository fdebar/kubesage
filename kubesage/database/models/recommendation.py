from uuid import uuid4

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class RecommendationModel(Base):
    __tablename__ = "finding_recommendations"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    finding = relationship("FindingModel", back_populates="recommendations")
