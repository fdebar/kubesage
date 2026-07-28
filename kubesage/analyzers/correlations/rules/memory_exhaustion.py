from kubesage.analyzers.correlations.base import BaseCorrelation
from kubesage.models.evidence import Evidence
from kubesage.models.finding import Finding, FindingKind, Severity


class MemoryExhaustionCorrelation(BaseCorrelation):
    rule_id = "memory_exhaustion"
    name = "Memory exhaustion"
    title = "Memory exhaustion detected"
    description = "The container was killed because it exceeded its memory limit."

    def apply(
        self,
        findings: list[Finding],
    ) -> list[Finding]:
        if not self._has(findings, "high_memory_usage"):
            return findings

        if not self._has(findings, "oom_killed"):
            return findings

        source = self._find(findings, "oom_killed")
        if source is None:
            return findings

        findings.append(
            Finding(
                rule=self.name,
                kind=FindingKind.DIAGNOSIS,
                severity=Severity.CRITICAL,
                title=self.title,
                description=self.description,
                resource=source.resource,
                structured_evidences=[
                    Evidence(
                        type="container_state",
                        name="termination_reason",
                        value="OOMKilled",
                    ),
                    Evidence(
                        type="correlation",
                        name="trigger",
                        value="high_memory_usage",
                    ),
                ],
                recommendations=[
                    "Increase memory limits if required.",
                    "Investigate memory leaks.",
                ],
                caused_by=[
                    "high_memory_usage",
                    "oom_killed",
                ],
                confidence=0.98,
            )
        )

        return findings
