from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.finding import (
    Finding,
    ResourceRef,
    Severity,
)
from kubesage.models.incident import Incident


class OOMKilledRule(BaseRule):
    category = RuleCategory.CONTAINER
    name = "OOMKilled"
    title = "Container terminated because of an Out Of Memory condition"
    description = (
        "The previous container execution was terminated by the kernel "
        "because it exceeded its memory limit."
    )

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        for container in incident.containers:
            if container.last_exit_reason != "OOMKilled":
                continue

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.HIGH,
                    title=self.title,
                    description=self.description,
                    resource=ResourceRef(
                        api_version="v1",
                        kind="Pod",
                        namespace=incident.namespace,
                        name=incident.pod,
                    ),
                    evidences=[
                        f"Container '{container.name}' last exit reason = OOMKilled.",
                        f"Restart count = {container.restart_count}",
                    ],
                    recommendations=[
                        "Review the container memory usage.",
                        "Increase the memory limit if appropriate.",
                        "Inspect the application for memory leaks.",
                    ],
                    metadata={
                        "container": container.name,
                        "last_exit_reason": container.last_exit_reason,
                        "restart_count": container.restart_count,
                    },
                )
            )

        return findings
