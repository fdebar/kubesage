from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import (
    Finding,
    FindingKind,
    Severity,
)
from kubesage.models.incident import Incident


class RestartRule(BaseRule):
    rule_id = "restart_count"
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
                    rule=self.rule_id,
                    severity=Severity.WARNING,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=self.description,
                    resource=self._pod_resource(incident),
                    structured_evidences=[
                        Evidence(
                            type=EvidenceType.CONTAINER_STATE,
                            name="restart_count",
                            value=str(container.restart_count),
                            source="kubernetes",
                            metadata={
                                "container": container.name,
                            },
                        ),
                        Evidence(
                            type=EvidenceType.THRESHOLD,
                            name="restart_threshold",
                            value=str(self.RESTART_THRESHOLD),
                            source="kubesage",
                        ),
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
                    priority=20,
                )
            )

        return findings
