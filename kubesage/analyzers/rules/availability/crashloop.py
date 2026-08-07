from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import (
    Finding,
    FindingKind,
    Severity,
)
from kubesage.models.incident import Incident


class CrashLoopRule(BaseRule):
    rule_id = "crashloop"
    name = "CrashLoopBackOff"
    description = "Detect CrashLoopBackOff"
    title = "Container is crashing"
    category = RuleCategory.CONTAINER

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        for container in incident.containers:
            if container.waiting_reason != "CrashLoopBackOff":
                continue

            evidences = [
                Evidence(
                    type=EvidenceType.CONTAINER_STATE,
                    name="waiting_reason",
                    value="CrashLoopBackOff",
                    source="kubernetes",
                    description=(
                        "The container is currently in CrashLoopBackOff, "
                        "indicating that Kubernetes is repeatedly restarting "
                        "the container after failed starts."
                    ),
                    metadata={
                        "container": container.name,
                    },
                ),
                Evidence(
                    type=EvidenceType.CONTAINER_STATE,
                    name="restart_count",
                    value=str(container.restart_count),
                    source="kubernetes",
                    description=(
                        f"The container has restarted {container.restart_count} times."
                    ),
                    metadata={
                        "container": container.name,
                    },
                ),
            ]

            if container.last_exit_code is not None:
                evidences.append(
                    Evidence(
                        type=EvidenceType.CONTAINER_STATE,
                        name="last_exit_code",
                        value=str(container.last_exit_code),
                        source="kubernetes",
                        description=(
                            f"The container's last termination exited "
                            f"with code {container.last_exit_code}."
                        ),
                        metadata={
                            "container": container.name,
                        },
                    )
                )

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.CRITICAL,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=self.description,
                    resource=self._pod_resource(incident),
                    recommendations=[
                        "Check the logs of the container to see what is causing the crash.",  # noqa
                        "Check the resources allocated to  the container to see if they are sufficient.",  # noqa
                    ],
                    structured_evidences=evidences,
                    priority=20,
                )
            )

        return findings
