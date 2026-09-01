from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident
from kubesage.models.prompt_context import PromptContext
from kubesage.models.timeline import TimelineEvent


class AIContext:
    def __init__(
        self,
        incident: Incident,
        findings: list[Finding],
        timeline: list[TimelineEvent] | None = None,
    ) -> None:
        self.ctx = PromptContext(
            namespace=incident.namespace,
            pod=incident.pod,
            phase=incident.phase,
            logs=incident.logs,
            events=incident.events,
            findings=findings,
            timeline=timeline or [],
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
    def evidences(self) -> list[dict[str, str | None]]:
        seen: set[str] = set()
        evidences: list[dict[str, str | None]] = []

        for finding in self.ctx.findings:
            for evidence in finding.structured_evidences:
                if evidence.id in seen:
                    continue

                seen.add(evidence.id)
                evidences.append(
                    {
                        "id": evidence.id,
                        "finding": finding.rule,
                        "type": evidence.type.value if evidence.type else None,
                        "name": evidence.name,
                        "value": evidence.value,
                        "source": evidence.source,
                        "description": evidence.description,
                    }
                )

        return evidences

    @property
    def root_causes(self) -> list[Finding]:
        diagnoses = self.diagnoses
        caused_diagnoses = {
            cause for diagnosis in diagnoses for cause in diagnosis.caused_by
        }

        return [
            diagnosis
            for diagnosis in diagnoses
            if diagnosis.rule not in caused_diagnoses
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
