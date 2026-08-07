from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import (
    Finding,
    FindingKind,
    Severity,
)
from kubesage.models.incident import Incident


class ImagePullRule(BaseRule):
    rule_id = "image_pull"
    title = "Container image cannot be pulled"
    description = "The container image cannot be downloaded."
    category = RuleCategory.CONTAINER

    WAITING_REASONS = {
        "ImagePullBackOff",
        "ErrImagePull",
    }

    def evaluate(self, incident: Incident) -> list[Finding]:

        findings: list[Finding] = []

        for container in incident.containers:
            if container.waiting_reason not in self.WAITING_REASONS:
                continue

            findings.append(
                Finding(
                    rule=self.rule_id,
                    severity=Severity.CRITICAL,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=self.description,
                    resource=self._pod_resource(incident),
                    recommendations=[
                        "Verify that the image exists.",
                        "Verify the image tag.",
                        "Verify the imagePullSecrets.",
                        "Verify registry connectivity and authentication.",
                    ],
                    structured_evidences=[
                        Evidence(
                            type=EvidenceType.CONTAINER_STATE,
                            name="waiting_reason",
                            value=container.waiting_reason,
                            source="kubernetes",
                            metadata={
                                "container": container.name,
                            },
                        ),
                        Evidence(
                            type=EvidenceType.EVENT,
                            name="waiting_message",
                            value=(
                                container.waiting_message
                                or "No additional Kubernetes message."
                            ),
                            source="kubernetes",
                            metadata={
                                "container": container.name,
                            },
                        ),
                    ],
                    metadata={
                        "container": container.name,
                        "reason": container.waiting_reason,
                    },
                    priority=20,
                )
            )

        return findings
