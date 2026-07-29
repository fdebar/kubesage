from kubesage.analyzers.correlations.base import BaseCorrelation
from kubesage.models.evidence import Evidence
from kubesage.models.finding import Finding, FindingKind, Severity


class CPUContentionCorrelation(BaseCorrelation):
    rule_id = "cpu_contention"
    name = "CPU contention"
    title = "CPU contention detected"
    description = (
        "The container is experiencing CPU contention because CPU "
        "usage is high and throttling is detected."
    )

    def apply(
        self,
        findings: list[Finding],
    ) -> list[Finding]:
        if not self._has(findings, "high_cpu_usage"):
            return findings

        if not self._has(findings, "cpu_throttling"):
            return findings

        cpu_finding = self._find(findings, "high_cpu_usage")
        if cpu_finding is None:
            return findings

        findings.append(
            Finding(
                rule=self.name,
                kind=FindingKind.DIAGNOSIS,
                severity=Severity.HIGH,
                title=self.title,
                description=self.description,
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
                structured_evidences=[
                    Evidence(
                        type="metric",
                        name="cpu_usage",
                        value="High CPU Usage",
                        source="kubernetes",
                    ),
                    Evidence(
                        type="correlation",
                        name="trigger",
                        value="high_cpu_usage",
                        source="kubesage",
                    ),
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
