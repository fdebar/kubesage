from analyzers.rules.base import BaseRule

from models.finding import (
    Finding,
    Severity,
)


class OOMRule(BaseRule):
    name = "OOM"
    description = "Detect OOMKilled"

    def evaluate(self, incident):
        findings = []

        for container in incident.containers:
            if container.last_exit_code == 137:
                findings.append(
                    Finding(
                        severity=Severity.CRITICAL.value,
                        title="OOMKilled detected",
                        description=(
                            f"{container.name} " "likely exceeded its memory limit."
                        ),
                        confidence=0.9,
                        source="kubernetes.container.exit_code",
                        category="oom",
                        evidence=["container.last_exit_code"],
                    )
                )

        return findings
