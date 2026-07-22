from kubesage.models.incident import Incident
from kubesage.analyzers.rules.base import BaseRule
from kubesage.models.finding import Finding, Severity


class HighCPURule(BaseRule):
    name = "High CPU"
    description = "Detect sustained CPU usage"

    CPU_THRESHOLD = 0.8

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        if incident.prometheus is None:
            return findings

        cpu = incident.prometheus.cpu
        if cpu is None:
            return findings

        if cpu.value > self.CPU_THRESHOLD:
            findings.append(
                Finding(
                    severity=Severity.WARNING,
                    title="CPU usage is high",
                    description=(f"CPU usage is {cpu.value:.2f} cores."),
                    confidence=0.80,
                    source="prometheus",
                    category="resource_utilization",
                    evidence=["cpu"],
                )
            )

        return findings
