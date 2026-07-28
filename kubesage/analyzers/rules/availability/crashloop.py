from kubesage.analyzers.rules.base import BaseRule, RuleCategory
from kubesage.models.finding import (
    Finding,
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
            if container.waiting_reason == "CrashLoopBackOff":
                findings.append(
                    Finding(
                        rule=self.name,
                        severity=Severity.CRITICAL,
                        title=self.title,
                        description=self.description,
                        resource=self._pod_resource(incident),
                        recommendations=[
                            "Check the logs of the container to see what is causing the crash.",  # noqa
                            "Check the resources allocated to  the container to see if they are sufficient.",  # noqa
                        ],
                        evidences=[
                            f"Container {container.name} waiting reason is CrashLoopBackOff.",  # noqa
                            f"Restart count = {container.restart_count}",  # noqa
                        ],
                        priority=20,
                    )
                )

        return findings
