from analyzers.rules.base import BaseRule
from models.finding import (
    Finding,
    Severity,
)


class HighMemoryRule(BaseRule):
    name = "HighMemory"
    description = "Detect high memory usage"

    def evaluate(self, incident):
        findings = []

        if incident.metrics is None:
            return findings

        for c in incident.metrics.containers:
            mem = c.memory
            if mem.endswith("Mi"):
                value = int(mem[:-2])
                if value > 500:
                    findings.append(
                        Finding(
                            severity=Severity.WARNING,
                            title="High memory usage",
                            description=f"{c.name} is using {mem}.",
                            confidence=0.8,
                            source="metrics-server",
                            category="resource_utilization",
                            evidence=["memory"],
                        )
                    )

        return findings
