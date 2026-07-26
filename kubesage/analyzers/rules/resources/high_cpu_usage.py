from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.finding import Finding, Severity
from kubesage.models.incident import Incident


class HighCPUUsageRule(BaseRule):
    name = "High CPU Usage"
    title = "Detect containers close to their CPU limit."
    description = "Detect containers close to their CPU limit."
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
            if (
                container.cpu_usage is None
                or container.cpu_limit is None
                or container.cpu_limit <= 0
            ):
                continue

            ratio = container.cpu_usage / container.cpu_limit
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
                        "of its CPU limit."
                    ),
                    resource=self._pod_resource(incident),
                    evidences=[
                        f"Container: {container.name}",
                        f"CPU usage: {container.cpu_usage:.3f} cores",
                        f"CPU limit: {container.cpu_limit:.3f} cores",
                        f"Usage ratio: {ratio:.2%}",
                    ],
                    recommendations=[
                        "Investigate CPU-intensive workloads.",
                        "Review CPU requests and limits.",
                        "Consider optimizing the application or increasing the CPU limit.",  # noqa: E501
                    ],
                    metadata={
                        "container": container.name,
                        "cpu_usage": container.cpu_usage,
                        "cpu_limit": container.cpu_limit,
                        "usage_ratio": ratio,
                    },
                    confidence=0.95,
                )
            )

        return findings
