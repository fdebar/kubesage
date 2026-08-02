from uuid import UUID

from kubesage.database.models.analysis import AnalysisModel
from kubesage.mappers.ai_report_mapper import AIReportMapper
from kubesage.mappers.finding_mapper import FindingMapper
from kubesage.models.analysis import Analysis
from kubesage.models.incident import Incident


class AnalysisMapper:
    @staticmethod
    def to_model(analysis: Analysis) -> AnalysisModel:
        """Map an Analysis to an AnalysisModel."""

        model = AnalysisModel(
            id=str(analysis.id),
            namespace=analysis.incident.namespace,
            pod=analysis.incident.pod,
            duration_ms=analysis.duration_ms,
            summary=analysis.report.summary if analysis.report else None,
        )

        model.findings = [
            FindingMapper.to_model(finding, str(analysis.id))
            for finding in analysis.findings
        ]

        if analysis.report:
            model.report = AIReportMapper.to_model(analysis.report, str(analysis.id))

        return model

    @staticmethod
    def to_domain(model: AnalysisModel) -> Analysis:
        """Convert an AnalysisModel to an Analysis."""

        return Analysis(
            id=UUID(model.id),
            incident=Incident(
                namespace=model.namespace,
                pod=model.pod,
                phase="",
            ),
            findings=[FindingMapper.to_domain(f) for f in model.findings],
            report=(AIReportMapper.to_domain(model.report) if model.report else None),
            duration_ms=model.duration_ms,
            created_at=model.created_at,
        )
