from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


class HighCPUUsageRule(BaseRule):
    rule_id = "high_cpu_usage"
    name = "High CPU Usage"
    title = "Detect containers close to their CPU limit."
    description = "Detect containers close to their CPU limit."
    category = RuleCategory.METRIC

    threshold = 0.80

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        for container in incident.containers:
            usage = container.usage
            resources = container.resources

            if usage is None or resources is None:
                continue

            if usage.cpu_usage is None or resources.cpu_limit is None:
                continue

            if resources.cpu_limit <= 0:
                continue

            ratio = usage.cpu_usage / resources.cpu_limit

            if ratio < self.threshold:
                continue

            evidences = [
                Evidence(
                    type=EvidenceType.METRIC,
                    name="cpu_usage",
                    value=str(usage.cpu_usage),
                    source="prometheus",
                    description=(
                        f"The container is currently using {usage.cpu_usage} CPU cores."
                    ),
                    unit="cores",
                    metadata={"container": container.name},
                ),
                Evidence(
                    type=EvidenceType.METRIC,
                    name="cpu_limit",
                    value=str(resources.cpu_limit),
                    source="kubernetes",
                    description=(
                        f"The container has a CPU limit of {resources.cpu_limit} cores."
                    ),
                    unit="cores",
                    metadata={"container": container.name},
                ),
                Evidence(
                    type=EvidenceType.METRIC,
                    name="cpu_usage_ratio",
                    value=str(ratio),
                    source="kubesage",
                    description=(
                        f"The container is using {ratio:.0%} "
                        "of its configured CPU limit."
                    ),
                    unit="ratio",
                    metadata={"container": container.name},
                ),
                Evidence(
                    type=EvidenceType.THRESHOLD,
                    name="cpu_usage_threshold",
                    value=str(self.threshold),
                    source="kubesage",
                    description=(
                        f"The finding is triggered when CPU usage reaches "
                        f"{self.threshold:.0%} of the configured CPU limit."
                    ),
                    unit="ratio",
                ),
            ]

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.WARNING,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=(
                        f"Container '{container.name}' "
                        f"is using {ratio:.0%} "
                        "of its CPU limit."
                    ),
                    resource=self._pod_resource(incident),
                    structured_evidences=evidences,
                    recommendations=[
                        "Investigate CPU-intensive workloads.",
                        "Review CPU requests and limits.",
                        "Consider optimizing the application or increasing the CPU limit.",  # noqa: E501
                    ],
                    metadata={
                        "container": container.name,
                        "cpu_usage": usage.cpu_usage,
                        "cpu_limit": resources.cpu_limit,
                        "usage_ratio": ratio,
                    },
                    confidence=0.95,
                    priority=20,
                )
            )

        return findings
