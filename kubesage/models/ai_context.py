from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import (
    Correlation,
    IncidentIntelligence,
    RootCauseCandidate,
)
from kubesage.models.prompt_context import PromptContext
from kubesage.services.finding_ranker import FindingRanker


class AIContext:
    def __init__(self, incident: Incident, intelligence: IncidentIntelligence) -> None:
        self.incident = incident
        self.intelligence = intelligence
        ranked_findings = FindingRanker().rank(intelligence.findings)

        self.ctx = PromptContext(
            namespace=incident.namespace,
            pod=incident.pod,
            phase=incident.phase,
            events=incident.events,
            findings=ranked_findings,
            timeline=intelligence.timeline,
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
    def root_causes(self) -> list[RootCauseCandidate]:
        return self.intelligence.root_causes

    @property
    def correlations(self) -> list[Correlation]:
        return self.intelligence.correlations

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

    @property
    def root_cause_evidence(self) -> dict[str, list[str]]:
        return {
            candidate.finding: candidate.supporting_evidence
            for candidate in self.intelligence.root_causes
        }
