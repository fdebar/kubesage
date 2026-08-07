from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


class HighMemoryUsageRule(BaseRule):
    rule_id = "high_memory_usage"
    title = "Detect containers close to their memory limit."
    description = "Detect containers close to their memory limit."
    category = RuleCategory.METRIC

    threshold = 0.80

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        for container in incident.containers:
            usage = container.usage
            resources = container.resources

            if usage is None or resources is None:
                continue

            if usage.memory_usage is None or resources.memory_limit is None:
                continue

            if resources.memory_limit <= 0:
                continue

            ratio = usage.memory_usage / resources.memory_limit
            if ratio < self.threshold:
                continue

            evidences = [
                Evidence(
                    type=EvidenceType.METRIC,
                    name="memory_usage",
                    value=str(usage.memory_usage),
                    source="prometheus",
                    description=(
                        f"The container is currently using "
                        f"{usage.memory_usage} bytes of memory."
                    ),
                    unit="bytes",
                    metadata={"container": container.name},
                ),
                Evidence(
                    type=EvidenceType.METRIC,
                    name="memory_limit",
                    value=str(resources.memory_limit),
                    source="kubernetes",
                    description=(
                        f"The container has a memory limit of "
                        f"{resources.memory_limit} bytes."
                    ),
                    unit="bytes",
                    metadata={"container": container.name},
                ),
                Evidence(
                    type=EvidenceType.METRIC,
                    name="memory_usage_ratio",
                    value=str(ratio),
                    source="kubesage",
                    description=(
                        f"The container is using {ratio:.0%} "
                        "of its configured memory limit."
                    ),
                    unit="ratio",
                    metadata={"container": container.name},
                ),
                Evidence(
                    type=EvidenceType.THRESHOLD,
                    name="memory_usage_threshold",
                    value=str(self.threshold),
                    source="kubesage",
                    description=(
                        f"The finding is triggered when memory usage reaches "
                        f"{self.threshold:.0%} of the configured memory limit."
                    ),
                    unit="ratio",
                ),
            ]

            findings.append(
                Finding(
                    rule=self.rule_id,
                    severity=Severity.WARNING,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=(
                        f"Container '{container.name}' "
                        f"is using {ratio:.0%} "
                        "of its memory limit."
                    ),
                    resource=self._pod_resource(incident),
                    structured_evidences=evidences,
                    recommendations=[
                        ("Investigate possible memory leaks."),
                        ("Increase memory limit if usage is expected."),
                    ],
                    metadata={
                        "container": container.name,
                        "memory_usage": usage.memory_usage,
                        "memory_limit": resources.memory_limit,
                        "usage_ratio": ratio,
                    },
                    confidence=0.95,
                    priority=20,
                )
            )

        return findings
