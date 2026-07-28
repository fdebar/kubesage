from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.finding import (
    Finding,
    ResourceRef,
    Severity,
)
from kubesage.models.incident import Incident


class PendingRule(BaseRule):
    rule_id = "pending"
    name = "Pending"
    title = "Pod cannot be scheduled"
    description = "The pod is pending because Kubernetes cannot schedule it."
    category = RuleCategory.EVENT

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        if incident.phase != "Pending":
            return findings

        for event in incident.events:
            if event.reason != "FailedScheduling":
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
                        f"Pod phase = {incident.phase}",
                        f"{event.reason}: {event.message}",
                    ],
                    recommendations=[
                        "Review the scheduler event message.",
                        "Check node resources (CPU, memory, ephemeral storage).",
                        "Verify node selectors, affinities and tolerations.",
                        "Verify PersistentVolumeClaims if applicable.",
                    ],
                    metadata={
                        "event_reason": event.reason,
                    },
                )
            )

        return findings
