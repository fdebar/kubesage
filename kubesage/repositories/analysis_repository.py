from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.finding import FindingModel
from kubesage.mappers.analysis_mapper import AnalysisMapper
from kubesage.mappers.analysis_summary_mapper import AnalysisSummaryMapper
from kubesage.models.analysis import Analysis
from kubesage.models.analysis_summary import AnalysisSummary


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

    def list_analyses(self, limit: int = 20, offset: int = 0) -> list[Analysis]:
        statement = (
            select(AnalysisModel)
            .order_by(AnalysisModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = self.session.execute(statement)
        models = result.scalars().all()

        return [AnalysisMapper.to_domain(m) for m in models]

    def list_summaries(self, limit: int = 20, offset: int = 0) -> list[AnalysisSummary]:
        statement = (
            select(AnalysisModel)
            .order_by(AnalysisModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = self.session.execute(statement)
        models = result.scalars().all()

        return [AnalysisSummaryMapper.to_domain(m) for m in models]

    def count(self) -> int:
        statement = select(func.count(AnalysisModel.id))
        count = self.session.scalar(statement)

        return count or 0

    def count_findings_by_severity(self, severity: str) -> int:
        statement = select(func.count(FindingModel.id)).where(
            FindingModel.severity == severity
        )
        count = self.session.scalar(statement)

        return count or 0

    def count_findings(self) -> int:
        statement = select(func.count(FindingModel.id))

        return self.session.scalar(statement) or 0
