from uuid import UUID

from kubesage.api.schemas.analysis_summary import AnalysisSummaryResponse
from kubesage.database.models.analysis import AnalysisModel
from kubesage.models.analysis_summary import AnalysisSummary
from kubesage.models.finding import Severity


class AnalysisSummaryMapper:
    @staticmethod
    def to_domain(model: AnalysisModel) -> AnalysisSummary:
        return AnalysisSummary(
            id=UUID(model.id),
            namespace=model.namespace,
            pod=model.pod,
            phase=model.phase,
            highest_severity=(
                Severity(model.highest_severity) if model.highest_severity else None
            ),
            summary=model.summary,
            findings_count=model.findings_count,
            duration_ms=model.duration_ms,
            created_at=model.created_at,
            trace_id=model.trace_id if model.trace_id else None,
        )

    @staticmethod
    def to_response(analyses: list[AnalysisSummary]) -> list[AnalysisSummaryResponse]:
        """Convert an AnalysisSummary list to an AnalysisSummaryResponse list."""

        return [
            AnalysisSummaryResponse(
                id=analysis.id,
                namespace=analysis.namespace,
                pod=analysis.pod,
                phase=analysis.phase,
                highest_severity=analysis.highest_severity,
                summary=analysis.summary,
                findings_count=analysis.findings_count,
                duration_ms=analysis.duration_ms,
                created_at=analysis.created_at,
                trace_id=analysis.trace_id,
            )
            for analysis in analyses
        ]
