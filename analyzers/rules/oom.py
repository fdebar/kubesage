from analyzers.rules.base import BaseRule

from models.finding import (
    Finding,
    Severity,
)


class OOMRule(BaseRule):

    def evaluate(self, incident):

        findings = []

        for container in incident.containers:

            if container.last_exit_code == 137:

                findings.append(
                    Finding(
                        severity=Severity.CRITICAL.value,
                        title="OOMKilled détecté",
                        description=(
                            f"{container.name} " "a probablement dépassé sa mémoire."
                        ),
                        confidence=0.9,
                        source="kubernetes.container.exit_code",
                    )
                )

        return findings
