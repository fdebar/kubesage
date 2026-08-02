from kubesage.database.models.ai_report import AIReportModel
from kubesage.models.ai_report import AIReport


class AIReportMapper:
    @staticmethod
    def to_domain(model: AIReportModel) -> AIReport:
        """Convert an AIReportModel to an AIReport."""

        return AIReport(
            summary=model.summary,
            root_cause=model.root_cause,
            evidence=[],
        )
