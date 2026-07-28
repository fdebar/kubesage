from kubesage.analyzers.rules.base import BaseRule
from kubesage.models.finding import Finding, Severity
from kubesage.models.incident import Incident


class MemoryPressureRule(BaseRule):
    rule_id = "memory_pressure"
    name = "Memory Pressure"
    title = "Detect Kubernetes memory pressure"
    description = "Detect Kubernetes memory pressure events impacting a pod."

    def evaluate(
        self,
        incident: Incident,
    ) -> list[Finding]:
        findings = []

        for event in incident.events:
            message = event.message.lower()

            if event.reason == "Evicted" and "memory" in message:
                findings.append(
                    Finding(
                        rule=self.name,
                        severity=Severity.HIGH,
                        title=self.title,
                        description=self.description,
                        resource=self._pod_resource(incident),
                        evidences=[
                            event.message,
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
