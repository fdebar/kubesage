from kubesage.analyzers.correlations.base import BaseCorrelation
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import (
    Finding,
    FindingKind,
    Severity,
)


class CrashLoopRootCauseCorrelation(BaseCorrelation):
    rule_id = "crash_loop_root_cause"
    name = "CrashLoop root cause"
    description = "The pod is restarting because it is exhausting available memory"
    title = "CrashLoop caused by memory exhaustion"

    def apply(
        self,
        findings: list[Finding],
    ) -> list[Finding]:
        if not self._has(findings, "crash_loop"):
            return findings

        if not self._has(findings, "memory_exhaustion"):
            return findings

        source = self._find(findings, "memory_exhaustion")
        if source is None:
            return findings

        findings.append(
            Finding(
                rule=self.name,
                kind=FindingKind.DIAGNOSIS,
                severity=Severity.CRITICAL,
                title=self.title,
                description=self.description,
                resource=source.resource,
                recommendations=[
                    "Increase memory limits.",
                    "Investigate application memory usage.",
                ],
                structured_evidences=[
                    Evidence(
                        type=EvidenceType.CONTAINER_STATE,
                        name="restart_reason",
                        value="CrashLoopBackOff",
                        source="kubernetes",
                        metadata={
                            "triggered_by": "crash_loop",
                        },
                    ),
                    Evidence(
                        type=EvidenceType.METRIC,
                        name="memory_exhaustion",
                        value="Memory limit exceeded",
                        source="prometheus",
                        metadata={
                            "triggered_by": "memory_exhaustion",
                        },
                    ),
                    Evidence(
                        type=EvidenceType.CORRELATION,
                        name="root_cause",
                        value="memory_exhaustion -> crash_loop",
                        source="kubesage",
                    ),
                ],
                caused_by=[
                    "crash_loop",
                    "memory_exhaustion",
                ],
                confidence=0.97,
                priority=90,
            )
        )

        return findings
