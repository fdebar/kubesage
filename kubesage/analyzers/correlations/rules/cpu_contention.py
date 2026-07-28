from kubesage.analyzers.correlations.base import BaseCorrelation
from kubesage.models.finding import Finding, FindingKind, Severity


class CPUContentionCorrelation(BaseCorrelation):
    rule_id = "cpu_contention"
    name = "CPU contention"
    description = "CPU contention detected"

    def apply(
        self,
        findings: list[Finding],
    ) -> list[Finding]:
        if not self._has(findings, "high_cpu_usage"):
            return findings

        if not self._has(findings, "cpu_throttling"):
            return findings

        cpu_finding = self._find(
            findings,
            "high_cpu_usage",
        )

        if cpu_finding is None:
            return findings

        findings.append(
            Finding(
                rule=self.name,
                kind=FindingKind.DIAGNOSIS,
                severity=Severity.HIGH,
                title="CPU contention detected",
                description=(
                    "The container is experiencing CPU contention "
                    "because CPU usage is high and throttling is detected."
                ),
                resource=cpu_finding.resource,
                evidences=[
                    "High CPU usage detected",
                    "CPU throttling detected",
                ],
                recommendations=[
                    "Increase CPU limits if workload requires it.",
                    "Investigate CPU-intensive operations.",
                    "Review pod CPU requests and limits.",
                ],
                caused_by=[
                    "high_cpu_usage",
                    "cpu_throttling",
                ],
                confidence=0.95,
                priority=90,
            )
        )

        return findings
