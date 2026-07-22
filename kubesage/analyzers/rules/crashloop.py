from kubesage.models.incident import Incident
from kubesage.analyzers.rules.base import BaseRule
from kubesage.models.finding import (
    Finding,
    Severity,
)


class CrashLoopRule(BaseRule):
    name = "CrashLoop"
    description = "Detect CrashLoopBackOff"

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        for container in incident.containers:
            if container.waiting_reason == "CrashLoopBackOff":
                findings.append(
                    Finding(
                        severity=Severity.CRITICAL,
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
