from typing import cast
from uuid import UUID

from sqlalchemy import select
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

    def get(self, analysis_id: UUID) -> AnalysisModel | None:
        statement = select(AnalysisModel).where(AnalysisModel.id == str(analysis_id))
        result = self.session.execute(statement)

        return cast(AnalysisModel, result.scalar_one_or_none())

    def list_recent(self, limit: int = 20) -> list[AnalysisModel] | None:
        statement = (
            select(AnalysisModel).order_by(AnalysisModel.created_at.desc()).limit(limit)
        )
        result = self.session.execute(statement)

        return list(result.scalars())
