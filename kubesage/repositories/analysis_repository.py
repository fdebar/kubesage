from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kubesage.database.models.analysis import AnalysisModel
from kubesage.mappers.analysis_mapper import AnalysisMapper
from kubesage.models.analysis import Analysis


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, analysis: Analysis) -> None:
        model = AnalysisMapper.to_model(analysis)
        self.session.add(model)
        self.session.commit()

    def get(self, analysis_id: UUID) -> Analysis | None:
        statement = select(AnalysisModel).where(AnalysisModel.id == str(analysis_id))
        result = self.session.execute(statement)

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return AnalysisMapper.to_domain(model)

    def list_recent(self, limit: int = 20) -> list[Analysis] | None:
        statement = (
            select(AnalysisModel).order_by(AnalysisModel.created_at.desc()).limit(limit)
        )
        result = self.session.execute(statement)

        models = result.scalars().all()
        return [AnalysisMapper.to_domain(m) for m in models]

    def count(self) -> int:
        statement = select(func.count(AnalysisModel.id))
        count = self.session.scalar(statement)

        return count or 0

    def count_by_severity(self, severity: str) -> int:
        statement = select(func.count(AnalysisModel.id)).where(
            AnalysisModel.highest_severity == severity
        )
        count = self.session.scalar(statement)

        return count or 0
