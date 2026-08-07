from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


class CPUThrottlingRule(BaseRule):
    rule_id = "cpu_throttling"
    name = "CPU Throttling"
    title = "Detect significant CPU throttling"
    description = "Detect containers experiencing significant CPU throttling"
    category = RuleCategory.METRIC

    threshold = 0.20

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        for container in incident.containers:
            usage = container.usage

            if usage is None:
                continue

            if usage.cpu_throttling_ratio is None:
                continue

            ratio = usage.cpu_throttling_ratio

            if ratio < self.threshold:
                continue

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.WARNING,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=(
                        f"Container '{container.name}' is experiencing "
                        f"{ratio:.0%} CPU throttling."
                    ),
                    resource=self._pod_resource(incident),
                    structured_evidences=[
                        Evidence(
                            type=EvidenceType.METRIC,
                            name="cpu_throttling_ratio",
                            value=str(ratio),
                            source="prometheus",
                            description=(
                                f"{ratio:.0%} of the container's CPU time "
                                "is being throttled."
                            ),
                            unit="ratio",
                            metadata={
                                "container": container.name,
                            },
                        ),
                        Evidence(
                            type=EvidenceType.THRESHOLD,
                            name="cpu_throttling_threshold",
                            value=str(self.threshold),
                            source="kubesage",
                            description=(
                                f"The finding is triggered when CPU "
                                f"throttling reaches {self.threshold:.0%}."
                            ),
                            unit="ratio",
                        ),
                    ],
                    recommendations=[
                        "Review the container CPU limit.",
                        "Investigate CPU-intensive workloads.",
                        "Consider increasing the CPU limit if appropriate.",
                    ],
                    metadata={
                        "container": container.name,
                        "cpu_throttling_ratio": ratio,
                    },
                    confidence=0.95,
                    priority=20,
                )
            )

        return findings
