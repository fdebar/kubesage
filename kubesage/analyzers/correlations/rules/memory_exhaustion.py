from kubesage.analyzers.correlations.base import BaseCorrelation
from kubesage.models.finding import Finding, Severity


class MemoryExhaustionCorrelation(BaseCorrelation):
    rule_id = "memory_exhaustion"
    name = "Memory exhaustion"
    description = "Memory exhaustion detected"

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
                severity=Severity.CRITICAL,
                title="Memory exhaustion detected",
                description=(
                    "The container was killed because it exceeded its memory limit."
                ),
                resource=source.resource,
                evidences=[
                    "OOMKilled detected",
                    "High memory usage detected",
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
