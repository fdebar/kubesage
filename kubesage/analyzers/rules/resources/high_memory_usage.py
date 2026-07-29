from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


class HighMemoryUsageRule(BaseRule):
    rule_id = "high_memory_usage"
    name = "High Memory Usage"
    title = "Detect containers close to their memory limit."
    description = "Detect containers close to their memory limit."
    category = RuleCategory.METRIC

    threshold = 0.80

    def evaluate(
        self,
        incident: Incident,
    ) -> list[Finding]:
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

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.WARNING,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=(
                        f"Container '{container.name}' "
                        f"is using {ratio:.0%} "
                        "of its memory limit."
                    ),
                    resource=self._pod_resource(incident),
                    structured_evidences=[
                        Evidence(
                            type=EvidenceType.METRIC,
                            name="memory_usage",
                            value=str(usage.memory_usage),
                            source="prometheus",
                            metadata={
                                "container": container.name,
                                "unit": "bytes",
                            },
                        ),
                        Evidence(
                            type=EvidenceType.METRIC,
                            name="memory_limit",
                            value=str(resources.memory_limit),
                            source="kubernetes",
                            metadata={
                                "container": container.name,
                                "unit": "bytes",
                            },
                        ),
                        Evidence(
                            type=EvidenceType.METRIC,
                            name="memory_usage_ratio",
                            value=str(ratio),
                            source="kubesage",
                            metadata={
                                "container": container.name,
                            },
                        ),
                        Evidence(
                            type=EvidenceType.THRESHOLD,
                            name="memory_usage_threshold",
                            value=str(self.threshold),
                            source="kubesage",
                        ),
                    ],
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
