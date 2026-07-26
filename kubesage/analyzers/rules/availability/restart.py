from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.finding import (
    Finding,
    Severity,
)
from kubesage.models.incident import Incident


class RestartRule(BaseRule):
    name = "RestartCount"
    title = "Container restarted multiple times"
    description = "The container has restarted more than the expected threshold."
    category = RuleCategory

    RESTART_THRESHOLD = 5

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        for container in incident.containers:
            if container.restart_count < self.RESTART_THRESHOLD:
                continue

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.WARNING,
                    title=self.title,
                    description=self.description,
                    resource=self._pod_resource(incident),
                    evidences=[
                        f"Container '{container.name}' restart count = {container.restart_count}.",  # noqa
                        f"Restart threshold = {self.RESTART_THRESHOLD}.",
                    ],
                    recommendations=[
                        "Inspect the container logs.",
                        "Review Kubernetes events.",
                        "Check whether the application exits unexpectedly.",
                    ],
                    metadata={
                        "container": container.name,
                        "restart_count": container.restart_count,
                    },
                )
            )

        return findings
