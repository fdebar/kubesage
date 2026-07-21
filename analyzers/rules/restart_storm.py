from models.incident import Incident
from analyzers.rules.base import BaseRule
from models.finding import Finding, Severity


class RestartStormRule(BaseRule):
    name = "Restart Storm"
    description = "Detect abnormal restart count"

    RESTART_THRESHOLD = 5

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        if incident.prometheus is None:
            return findings

        restarts = incident.prometheus.restarts
        if restarts is None:
            return findings

        if restarts.value > self.RESTART_THRESHOLD:
            findings.append(
                Finding(
                    severity=Severity.CRITICAL,
                    title="Container restarted many times",
                    description=(f"{restarts.value:.0f} restarts detected."),
                    confidence=0.95,
                    source="prometheus",
                    category="stability",
                    evidence=["restarts"],
                )
            )

        return findings
