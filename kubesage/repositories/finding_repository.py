from opentelemetry import trace
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.finding import FindingModel
from kubesage.mappers.finding_list_item_mapper import FindingListItemMapper
from kubesage.models.finding_list_item import FindingListItem

tracer = trace.get_tracer(__name__)


class FindingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_findings(self, limit: int = 50, offset: int = 0) -> list[FindingListItem]:
        with tracer.start_as_current_span("database.list_findings") as span:
            span.set_attribute("findings.limit", limit)
            span.set_attribute("findings.offset", offset)

            statement = (
                select(FindingModel, AnalysisModel.created_at)
                .join(
                    AnalysisModel,
                    FindingModel.analysis_id == AnalysisModel.id,
                )
                .order_by(AnalysisModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )

            result = self.session.execute(statement)

            findings = [
                FindingListItemMapper.to_domain(
                    finding,
                    created_at,
                )
                for finding, created_at in result.all()
            ]

            span.set_attribute("findings.result.count", len(findings))

            return findings

    def count(self) -> int:
        with tracer.start_as_current_span("database.count_findings") as span:
            statement = select(func.count(FindingModel.id))
            count = self.session.scalar(statement) or 0

            span.set_attribute("findings.count", count)

            return count
