from analyzers.rules.base import BaseRule
from models.finding import Finding, Severity


class ProbableOOMRule(BaseRule):
    name = "Probable OOM"
    description = "Correlate memory and restart"

    def evaluate(self, incident):
        findings = []

        if incident.prometheus is None:
            return findings

        memory = incident.prometheus.memory
        if memory is None:
            return findings

        for container in incident.containers:
            if (
                container.waiting_reason == "CrashLoopBackOff"
                and container.last_exit_code == 137
            ):

                findings.append(
                    Finding(
                        severity=Severity.CRITICAL,
                        title="Probable OOMKilled",
                        description=(
                            "CrashLoopBackOff + exit code 137 "
                            "indicate an OOM condition."
                        ),
                        confidence=0.98,
                        source="correlation",
                        category="oom",
                        evidence=[
                            "container.waiting_reason",
                            "container.last_exit_code",
                        ],
                    )
                )

        return findings
