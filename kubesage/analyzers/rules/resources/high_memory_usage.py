from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.finding import Finding, Severity
from kubesage.models.incident import Incident


class HighMemoryUsageRule(BaseRule):
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

        if incident.prometheus is None:
            return findings

        for container in incident.prometheus.containers:
            if container.memory_usage is None or container.memory_limit is None:
                continue

            ratio = container.memory_usage / container.memory_limit
            if ratio < self.threshold:
                continue

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.WARNING,
                    title=self.title,
                    description=(
                        f"Container '{container.name}' "
                        f"is using {ratio:.0%} "
                        "of its memory limit."
                    ),
                    resource=self._pod_resource(incident),
                    evidences=[
                        f"Container: {container.name}",
                        (f"Memory usage: {container.memory_usage} bytes"),
                        (f"Memory limit: {container.memory_limit} bytes"),
                        (f"Usage ratio: {ratio:.2%}"),
                    ],
                    recommendations=[
                        ("Investigate possible memory leaks."),
                        ("Increase memory limit if usage is expected."),
                    ],
                    metadata={
                        "container": container.name,
                        "memory_usage": (container.memory_usage),
                        "memory_limit": (container.memory_limit),
                        "usage_ratio": ratio,
                    },
                    confidence=0.95,
                )
            )

        return findings
