from kubesage.analyzers.rules.base import BaseRule
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


class MemoryPressureRule(BaseRule):
    rule_id = "memory_pressure_eviction"
    name = "Memory Pressure Eviction"
    title = "Detect Kubernetes memory pressure eviction"
    description = "Detect Kubernetes memory pressure eviction events."

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings = []

        for event in incident.events:
            message = event.message.lower()

            if event.reason != "Evicted" or "memory" not in message:
                continue

            findings.append(
                Finding(
                    rule=self.name,
                    severity=Severity.HIGH,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=self.description,
                    resource=self._pod_resource(incident),
                    structured_evidences=[
                        Evidence(
                            type=EvidenceType.EVENT,
                            name="eviction_reason",
                            value=event.message,
                            source="kubernetes",
                            description=(
                                "Kubernetes evicted the pod because the node "
                                "was experiencing memory pressure."
                            ),
                            metadata={
                                "reason": event.reason,
                            },
                        ),
                    ],
                    recommendations=[
                        "Increase node memory capacity.",
                        "Review pod memory requests.",
                        "Investigate memory consuming workloads.",
                    ],
                    confidence=0.95,
                    priority=20,
                )
            )

        return findings
