from analyzers.rules.base import BaseRule
from models.finding import (
    Finding,
    Severity,
)


class CrashLoopRule(BaseRule):
    name = "CrashLoop"
    description = "Detect CrashLoopBackOff"

    def evaluate(self, incident):
        findings = []

        for container in incident.containers:

            if container.waiting_reason == "CrashLoopBackOff":

                findings.append(
                    Finding(
                        severity=Severity.CRITICAL.value,
                        title="CrashLoopBackOff detected",
                        description=(
                            f"The container {container.name} "
                            "is restarting continuously."
                        ),
                        confidence=0.95,
                        source="kubernetes.container.status",
                        category="crashloop",
                        evidence=[
                            "container.waiting_reason",
                            "container.last_exit_code",
                        ],
                    )
                )

        return findings
