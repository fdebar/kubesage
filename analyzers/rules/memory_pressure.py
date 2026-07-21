from models.incident import Incident
from analyzers.rules.base import BaseRule
from models.finding import Finding, Severity


class MemoryPressureRule(BaseRule):
    name = "Memory Pressure"
    description = "Detect high memory usage"

    LIMIT = 800 * 1024 * 1024

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        if incident.prometheus is None:
            return findings

        memory = incident.prometheus.memory
        if memory is None:
            return findings

        if memory.value > self.LIMIT:
            findings.append(
                Finding(
                    severity=Severity.WARNING,
                    title="High memory usage",
                    description=(f"{memory.value / 1024 / 1024:.0f} MiB used."),
                    confidence=0.8,
                    source="prometheus",
                    category="resource_utilization",
                    evidence=["memory"],
                )
            )

        return findings
