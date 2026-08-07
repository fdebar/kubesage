from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import (
    Finding,
    FindingKind,
    ResourceRef,
    Severity,
)
from kubesage.models.incident import Incident


class PendingRule(BaseRule):
    rule_id = "pending"
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
                            type=EvidenceType.POD_STATE,
                            name="phase",
                            value="Pending",
                            source="kubernetes",
                        ),
                        Evidence(
                            type=EvidenceType.EVENT,
                            name="scheduling_failure",
                            value=event.message,
                            source="kubernetes",
                            metadata={
                                "reason": event.reason,
                            },
                        ),
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
                    priority=20,
                )
            )

        return findings
