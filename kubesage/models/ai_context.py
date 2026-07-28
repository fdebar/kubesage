from dataclasses import dataclass, field

from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


@dataclass(slots=True)
class AIContext:
    incident: Incident
    findings: list[Finding] = field(default_factory=list)
    metrics_summary: str = ""

    @property
    def highest_severity(self) -> Severity | None:
        if not self.findings:
            return None
        return max(self.findings, key=lambda f: f.severity.weight).severity

    @property
    def recommendations(self) -> list[str]:
        seen: set[str] = set()
        recommendations: list[str] = []

        for finding in self.findings:
            for recommendation in finding.recommendations:
                if recommendation not in seen:
                    seen.add(recommendation)
                    recommendations.append(recommendation)

        return recommendations

    @property
    def evidences(self) -> list[str]:
        seen: set[str] = set()
        evidences: list[str] = []

        for finding in self.findings:
            for evidence in finding.structured_evidences:
                key = f"{finding.rule}:{evidence.name}:{evidence.value}"

                if key not in seen:
                    seen.add(key)
                    evidences.append(
                        f"{finding.rule}: {evidence.name}={evidence.value}"
                    )

        return evidences

    @property
    def root_causes(self) -> list[Finding]:
        return [
            finding
            for finding in self.findings
            if finding.kind == FindingKind.DIAGNOSIS
            and finding.severity == Severity.CRITICAL
        ]

    @property
    def symptoms(self) -> list[Finding]:
        return [
            finding
            for finding in self.findings
            if finding.kind == FindingKind.OBSERVATION
        ]

    @property
    def diagnoses(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.kind == "diagnosis"]

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)
