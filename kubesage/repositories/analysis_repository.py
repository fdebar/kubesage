from uuid import UUID

from opentelemetry import trace
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.finding import FindingModel
from kubesage.mappers.analysis_mapper import AnalysisMapper
from kubesage.mappers.analysis_summary_mapper import AnalysisSummaryMapper
from kubesage.mappers.incident_intelligence_mapper import (
    IncidentIntelligenceMapper,
)
from kubesage.models.analysis import Analysis
from kubesage.models.analysis_summary import AnalysisSummary

tracer = trace.get_tracer(__name__)


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, analysis: Analysis) -> None:
        with tracer.start_as_current_span("database.save_analysis") as span:
            try:
                span.set_attribute("analysis.findings.count", len(analysis.findings))
                span.set_attribute("analysis.has_report", analysis.report is not None)

                model = AnalysisMapper.to_model(analysis)
                model.correlations = IncidentIntelligenceMapper.correlations_to_models(
                    analysis.intelligence.correlations,
                    str(analysis.id),
                )
                model.root_causes = IncidentIntelligenceMapper.root_causes_to_models(
                    analysis.intelligence.root_causes,
                    str(analysis.id),
                )
                self.session.add(model)
                self.session.commit()

            except SQLAlchemyError as exc:
                self.session.rollback()
                span.record_exception(exc)
                raise

    def get(self, analysis_id: UUID) -> Analysis | None:
        with tracer.start_as_current_span("database.get_analysis") as span:
            try:
                span.set_attribute("analysis.id", str(analysis_id))

                statement = select(AnalysisModel).where(
                    AnalysisModel.id == str(analysis_id)
                )
                result = self.session.execute(statement)

                model = result.scalar_one_or_none()
                if model is None:
                    return None

                return AnalysisMapper.to_domain(model)

            except SQLAlchemyError as exc:
                span.record_exception(exc)
                raise

    def list_analyses(self, limit: int = 20, offset: int = 0) -> list[Analysis]:
        with tracer.start_as_current_span("database.list_analyses") as span:
            try:
                span.set_attribute("analysis.limit", limit)
                span.set_attribute("analysis.offset", offset)

                statement = (
                    select(AnalysisModel)
                    .order_by(AnalysisModel.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
                result = self.session.execute(statement)
                models = result.scalars().all()

                return [AnalysisMapper.to_domain(m) for m in models]

            except SQLAlchemyError as exc:
                span.record_exception(exc)
                raise

    def list_summaries(self, limit: int = 20, offset: int = 0) -> list[AnalysisSummary]:
        with tracer.start_as_current_span("database.list_summaries") as span:
            try:
                span.set_attribute("analysis.limit", limit)
                span.set_attribute("analysis.offset", offset)

                statement = (
                    select(AnalysisModel)
                    .order_by(AnalysisModel.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
                result = self.session.execute(statement)
                models = result.scalars().all()

                return [AnalysisSummaryMapper.to_domain(m) for m in models]

            except SQLAlchemyError as exc:
                span.record_exception(exc)
                raise

    def count(self) -> int:
        with tracer.start_as_current_span("database.count_analyses") as span:
            try:
                statement = select(func.count(AnalysisModel.id))
                count = self.session.scalar(statement)

                span.set_attribute("analysis.count", count or 0)

                return count or 0

            except SQLAlchemyError as exc:
                span.record_exception(exc)
                raise

    def count_findings_by_severity(self, severity: str) -> int:
        with tracer.start_as_current_span(
            "database.count_findings_by_severity"
        ) as span:
            try:
                span.set_attribute("analysis.severity", severity)

                statement = select(func.count(FindingModel.id)).where(
                    FindingModel.severity == severity
                )
                count = self.session.scalar(statement)

                span.set_attribute("analysis.count", count or 0)

                return count or 0

            except SQLAlchemyError as exc:
                span.record_exception(exc)
                raise

    def count_findings(self) -> int:
        with tracer.start_as_current_span("database.count_findings") as span:
            try:
                statement = select(func.count(FindingModel.id))
                count = self.session.scalar(statement)

                span.set_attribute("analysis.count", count or 0)

                return count or 0

            except SQLAlchemyError as exc:
                span.record_exception(exc)
                raise
