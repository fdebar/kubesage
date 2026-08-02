from kubesage.database.models.finding import FindingModel
from kubesage.models.finding import Finding, FindingKind, Severity


class FindingMapper:
    @staticmethod
    def to_model(finding: Finding, analysis_id: str) -> FindingModel:
        """Map a Finding to a FindingModel."""

        return FindingModel(
            analysis_id=analysis_id,
            rule=finding.rule,
            kind=finding.kind.value,
            severity=finding.severity.value,
            title=finding.title,
            description=finding.description,
        )

    @staticmethod
    def to_domain(model: FindingModel) -> Finding:
        """Convert a FindingModel to a Finding."""

        return Finding(
            rule=model.rule,
            kind=FindingKind(model.kind),
            severity=Severity(model.severity),
            title=model.title,
            description=model.description,
        )
