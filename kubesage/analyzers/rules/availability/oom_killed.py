from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity
from kubesage.models.incident import Incident


class OOMKilledRule(BaseRule):
    rule_id = "oom_killed"
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

            evidences = [
                Evidence(
                    type=EvidenceType.CONTAINER_STATE,
                    name="last_exit_reason",
                    value="OOMKilled",
                    source="kubernetes",
                    description=(
                        "The previous container execution was terminated "
                        "because of an out-of-memory condition."
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
                    description=_restart_description(container.restart_count),
                    metadata={
                        "container": container.name,
                    },
                ),
            ]

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.HIGH,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=self.description,
                    resource=ResourceRef(
                        api_version="v1",
                        kind="Pod",
                        namespace=incident.namespace,
                        name=incident.pod,
                    ),
                    structured_evidences=evidences,
                    recommendations=[
                        "Review the container memory usage.",
                        "Increase the memory limit if appropriate.",
                        "Inspect the application for memory leaks.",
                    ],
                    metadata={"container": container.name},
                    priority=20,
                )
            )

        return findings


def _restart_description(restart_count: int) -> str:
    noun = "time" if restart_count == 1 else "times"

    return f"The container has restarted {restart_count} {noun}."
