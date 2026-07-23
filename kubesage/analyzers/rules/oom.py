from kubesage.analyzers.rules.base import BaseRule
from kubesage.models.finding import (
    Finding,
    Severity,
)
from kubesage.models.incident import Incident


class OOMRule(BaseRule):
    name = "OOM"
    description = "Detect OOMKilled"

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        for container in incident.containers:
            if container.last_exit_code == 137:
                findings.append(
                    Finding(
                        severity=Severity.CRITICAL,
                        title="OOMKilled detected",
                        description=(
                            f"{container.name} likely exceeded its memory limit."
                        ),
                        confidence=0.9,
                        source="kubernetes.container.exit_code",
                        category="oom",
                        evidence=["container.last_exit_code"],
                    )
                )

        return findings
