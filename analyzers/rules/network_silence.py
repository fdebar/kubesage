from analyzers.rules.base import BaseRule
from models.finding import Finding, Severity


class NetworkSilenceRule(BaseRule):
    name = "Network Silence"
    description = "Detect no incoming traffic"

    def evaluate(self, incident):
        findings = []

        if incident.prometheus is None:
            return findings

        rx = incident.prometheus.network_rx
        if rx is None:
            return findings

        if rx.value < 1:
            findings.append(
                Finding(
                    severity=Severity.INFO,
                    title="No incoming traffic",
                    description=("No network traffic detected."),
                    confidence=0.70,
                    source="prometheus",
                    category="network",
                    evidence=["network_rx"],
                )
            )

        return findings
