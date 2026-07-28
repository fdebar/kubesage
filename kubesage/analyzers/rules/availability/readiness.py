from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.finding import (
    Finding,
    ResourceRef,
    Severity,
)
from kubesage.models.incident import Incident


class ReadinessRule(BaseRule):
    rule_id = "readiness"
    name = "Readiness"
    title = "Container is not Ready"
    description = "The container is not ready to receive traffic."
    category = RuleCategory.CONTAINER

    def evaluate(
        self,
        incident: Incident,
    ) -> list[Finding]:

        findings: list[Finding] = []

        for container in incident.containers:
            if container.ready:
                continue

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.WARNING,
                    title=self.title,
                    description=self.description,
                    resource=ResourceRef(
                        api_version="v1",
                        kind="Pod",
                        namespace=incident.namespace,
                        name=incident.pod,
                    ),
                    evidences=[
                        f"Container '{container.name}' ready = False.",
                    ],
                    recommendations=[
                        "Inspect the readiness probe configuration.",
                        "Check the application startup logs.",
                        "Verify dependencies such as databases or external services.",
                    ],
                    metadata={
                        "container": container.name,
                    },
                    priority=20,
                )
            )

        return findings
