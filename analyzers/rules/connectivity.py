from config import logger
from analyzers.rules.base import BaseRule
from models.finding import (
    Finding,
    Severity,
)


class ConnectivityRule(BaseRule):
    name = "Connectivity"
    description = "Detect connection refused"

    def evaluate(self, incident):
        findings = []

        logs = incident.logs.lower()
        if incident.logs is None:
            logger.warning("No logs collected")
            return findings

        if "connection refused" in logs:
            findings.append(
                Finding(
                    severity=Severity.WARNING.value,
                    title="Connection refused",
                    description=("An external dependency is refusing the connection."),
                    confidence=0.8,
                    source="container.logs",
                    category="connectivity",
                    evidence=["container.logs"],
                )
            )

        return findings
