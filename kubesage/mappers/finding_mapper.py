from kubesage.database.models.finding import FindingModel
from kubesage.models.finding import Finding


class FindingMapper:
    @staticmethod
    def to_model(
        finding: Finding,
        analysis_id: str,
    ) -> FindingModel:
        """Map a Finding to a FindingModel."""

        return FindingModel(
            analysis_id=analysis_id,
            rule=finding.rule,
            kind=finding.kind.value,
            severity=finding.severity.value,
            title=finding.title,
            description=finding.description,
        )
