from dataclasses import dataclass, field

from kubesage.models.finding import Finding, Severity
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
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)
