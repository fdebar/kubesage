from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import (
    Finding,
    FindingKind,
    ResourceRef,
    Severity,
)
from kubesage.models.incident import Incident


class ReadinessRule(BaseRule):
    rule_id = "readiness"
    title = "Container is not Ready"
    description = "The container is not ready to receive traffic."
    category = RuleCategory.CONTAINER

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        for container in incident.containers:
            if container.ready:
                continue

            findings.append(
                Finding(
                    rule=self.rule_id,
                    severity=Severity.WARNING,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=self.description,
                    resource=ResourceRef(
                        api_version="v1",
                        kind="Pod",
                        namespace=incident.namespace,
                        name=incident.pod,
                    ),
                    structured_evidences=[
                        Evidence(
                            type=EvidenceType.CONTAINER_STATE,
                            name="ready",
                            value="False",
                            source="kubernetes",
                            metadata={
                                "container": container.name,
                            },
                        ),
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
