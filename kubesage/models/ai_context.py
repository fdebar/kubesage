from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident
from kubesage.models.prompt_context import PromptContext


class AIContext:
    def __init__(self, incident: Incident, findings: list[Finding]):
        self.ctx = PromptContext(
            namespace=incident.namespace,
            pod=incident.pod,
            phase=incident.phase,
            logs=incident.logs,
            events=incident.events,
            findings=findings,
        )

    @property
    def highest_severity(self) -> Severity | None:
        if not self.ctx.findings:
            return None
        return max(self.ctx.findings, key=lambda f: f.severity.weight).severity

    @property
    def recommendations(self) -> list[str]:
        seen: set[str] = set()
        recommendations: list[str] = []

        for finding in self.ctx.findings:
            for recommendation in finding.recommendations:
                if recommendation not in seen:
                    seen.add(recommendation)
                    recommendations.append(recommendation)

        return recommendations

    @property
    def evidences(self) -> list[str]:
        seen: set[str] = set()
        evidences: list[str] = []

        for finding in self.ctx.findings:
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
            f
            for f in self.ctx.findings
            if f.kind == FindingKind.DIAGNOSIS and f.severity == Severity.CRITICAL
        ]

    @property
    def observations(self) -> list[Finding]:
        return [f for f in self.ctx.findings if f.kind == FindingKind.OBSERVATION]

    @property
    def diagnoses(self) -> list[Finding]:
        return [f for f in self.ctx.findings if f.kind == FindingKind.DIAGNOSIS]

    @property
    def finding_count(self) -> int:
        return len(self.ctx.findings)

    @property
    def has_findings(self) -> bool:
        return bool(self.ctx.findings)
