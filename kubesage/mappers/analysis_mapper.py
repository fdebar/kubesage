from kubesage.database.models.analysis import AnalysisModel
from kubesage.mappers.finding_mapper import FindingMapper
from kubesage.models.analysis import Analysis


class AnalysisMapper:
    @staticmethod
    def to_model(
        analysis: Analysis,
    ) -> AnalysisModel:
        """Map an Analysis to an AnalysisModel."""

        model = AnalysisModel(
            id=str(analysis.id),
            namespace=analysis.incident.namespace,
            pod=analysis.incident.pod,
            duration_ms=analysis.duration_ms,
            summary=analysis.report.summary,
        )

        model.findings = [
            FindingMapper.to_model(finding, str(analysis.id))
            for finding in analysis.findings
        ]

        return model
