import re

from kubesage.analyzers.rules.base import BaseRule
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


class ApplicationErrorRule(BaseRule):
    rule_id = "application_error"
    title = "Detect application errors"
    description = "Detect application errors reported in application logs."

    _PATTERNS = (
        re.compile(r"\berror\b", re.IGNORECASE),
        re.compile(r"\b(?:\w+)?exception\b", re.IGNORECASE),
        re.compile(r"\btraceback\b", re.IGNORECASE),
        re.compile(r"\bHTTP\s+5\d{2}\b", re.IGNORECASE),
        re.compile(r"\bconnection\s+refused\b", re.IGNORECASE),
        re.compile(r"\btimeout\b", re.IGNORECASE),
    )

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        if not incident.loki_logs:
            return []

        for entry in incident.loki_logs.entries:
            if not self._is_application_error(entry.message):
                continue

            findings.append(
                Finding(
                    rule=self.rule_id,
                    severity=Severity.ERROR,
                    kind=FindingKind.OBSERVATION,
                    title=self.title,
                    description=self.description,
                    resource=self._pod_resource(incident),
                    structured_evidences=[
                        Evidence(
                            type=EvidenceType.LOG,
                            name="application_error",
                            value=entry.message,
                            source="loki",
                            description="Application error detected in Loki logs.",
                            metadata={
                                "timestamp": entry.timestamp.isoformat(),
                                "labels": entry.labels,
                            },
                        )
                    ],
                    confidence=0.90,
                    priority=30,
                )
            )

        return findings

    def _is_application_error(self, message: str) -> bool:
        return any(pattern.search(message) for pattern in self._PATTERNS)
