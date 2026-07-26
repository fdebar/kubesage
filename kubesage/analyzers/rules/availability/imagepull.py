from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.finding import (
    Finding,
    Severity,
)
from kubesage.models.incident import Incident


class ImagePullRule(BaseRule):
    name = "ImagePull"
    title = "Container image cannot be pulled"
    description = "The container image cannot be downloaded."
    category = RuleCategory.CONTAINER

    WAITING_REASONS = {
        "ImagePullBackOff",
        "ErrImagePull",
    }

    def evaluate(
        self,
        incident: Incident,
    ) -> list[Finding]:

        findings: list[Finding] = []

        for container in incident.containers:
            if container.waiting_reason not in self.WAITING_REASONS:
                continue

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.CRITICAL,
                    title=self.title,
                    description=self.description,
                    resource=self._pod_resource(incident),
                    evidences=[
                        (
                            f"Container '{container.name}' "
                            f"waiting reason = {container.waiting_reason}"
                        ),
                        container.waiting_message
                        or "No additional Kubernetes message.",
                    ],
                    recommendations=[
                        "Verify that the image exists.",
                        "Verify the image tag.",
                        "Verify the imagePullSecrets.",
                        "Verify registry connectivity and authentication.",
                    ],
                    metadata={
                        "container": container.name,
                        "reason": container.waiting_reason,
                    },
                )
            )

        return findings
