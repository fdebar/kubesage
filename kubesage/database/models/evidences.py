from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class EvidenceModel(Base):
    __tablename__ = "finding_evidences"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evidence_metadata: Mapped[dict] = mapped_column(
        "metadata", JSON, nullable=True, default=dict
    )
    finding = relationship("FindingModel", back_populates="evidences")
