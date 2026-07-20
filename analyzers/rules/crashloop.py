from analyzers.rules.base import BaseRule

from models.finding import (
    Finding,
    Severity,
)


class CrashLoopRule(BaseRule):

    def evaluate(self, incident):

        findings = []

        for container in incident.containers:

            if container.waiting_reason == "CrashLoopBackOff":

                findings.append(
                    Finding(
                        severity=Severity.CRITICAL.value,
                        title="CrashLoopBackOff détecté",
                        description=(
                            f"Le container {container.name} "
                            "redémarre continuellement."
                        ),
                        confidence=0.95,
                        source="kubernetes.container.status",
                    )
                )

        return findings
