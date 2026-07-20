from analyzers.rules.base import BaseRule

from models.finding import (
    Finding,
    Severity,
)


class ConnectivityRule(BaseRule):

    def evaluate(self, incident):

        findings = []

        logs = incident.logs.lower()

        if "connection refused" in logs:

            findings.append(
                Finding(
                    severity=Severity.WARNING.value,
                    title="Connection refused",
                    description=("An external dependency is refusing the connection."),
                    confidence=0.8,
                    source="container.logs",
                )
            )

        return findings
