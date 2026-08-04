from uuid import uuid4

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kubesage.database.base import Base


class IncidentSnapshotModel(Base):
    __tablename__ = "incident_snapshots"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    analysis = relationship("AnalysisModel", back_populates="incident_snapshot")
