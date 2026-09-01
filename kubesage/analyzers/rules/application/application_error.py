from kubesage.analyzers.application_error import (
    ApplicationErrorClassification,
    ApplicationErrorClassifier,
    ApplicationErrorDomain,
    ApplicationErrorKind,
)
from kubesage.analyzers.rules.base import BaseRule
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


class ApplicationErrorRule(BaseRule):
    rule_id = "application_error"
    title = "Detect application errors"
    description = "Detect application errors reported in application logs."
    classifier = ApplicationErrorClassifier()

    def evaluate(self, incident: Incident) -> list[Finding]:
        findings: list[Finding] = []

        if not incident.loki_logs:
            return []

        for entry in incident.loki_logs.entries:
            classification = self.classifier.classify(entry.message)
            if classification is None:
                continue

            evidence_metadata = {
                "error_kind": classification.kind.value,
                "timestamp": entry.timestamp.isoformat(),
                "labels": entry.labels,
            }
            finding_metadata = {
                "error_kind": classification.kind.value,
                "log_timestamp": entry.timestamp.isoformat(),
            }
            if classification.domain:
                evidence_metadata["error_domain"] = classification.domain.value
                finding_metadata["error_domain"] = classification.domain.value

            findings.append(
                Finding(
                    rule=self.rule_id,
                    severity=Severity.ERROR,
                    kind=FindingKind.OBSERVATION,
                    title=self._title(classification),
                    description=self._description(classification, entry.message),
                    metadata=finding_metadata,
                    resource=self._pod_resource(incident),
                    structured_evidences=[
                        Evidence(
                            type=EvidenceType.LOG,
                            name="application_error",
                            value=entry.message,
                            source="loki",
                            description="Application error detected in Loki logs.",
                            metadata=evidence_metadata,
                        )
                    ],
                    confidence=0.90,
                    priority=30,
                )
            )

        return findings

    def _title(self, classification: ApplicationErrorClassification) -> str:
        if classification.domain == ApplicationErrorDomain.DATABASE:
            database_titles = {
                ApplicationErrorKind.CONNECTION_ERROR: "Database connection failure",
                ApplicationErrorKind.TIMEOUT: "Database timeout",
                ApplicationErrorKind.HTTP_5XX: "Database HTTP 5xx error",
                ApplicationErrorKind.EXCEPTION: "Database exception",
                ApplicationErrorKind.GENERIC_ERROR: "Database error",
            }

            return database_titles[classification.kind]

        titles = {
            ApplicationErrorKind.CONNECTION_ERROR: "Application connection failure",
            ApplicationErrorKind.TIMEOUT: "Application timeout",
            ApplicationErrorKind.HTTP_5XX: "HTTP 5xx error",
            ApplicationErrorKind.EXCEPTION: "Application exception",
            ApplicationErrorKind.GENERIC_ERROR: "Application error",
        }

        return titles[classification.kind]

    def _description(
        self,
        classification: ApplicationErrorClassification,
        message: str,
    ) -> str:
        if classification.domain == ApplicationErrorDomain.DATABASE:
            descriptions = {
                ApplicationErrorKind.CONNECTION_ERROR: (
                    "Application logs report a database connection failure."
                ),
                ApplicationErrorKind.TIMEOUT: (
                    "Application logs report a database timeout."
                ),
                ApplicationErrorKind.HTTP_5XX: (
                    "Application logs report a database-related HTTP 5xx error."
                ),
                ApplicationErrorKind.EXCEPTION: (
                    "Application logs report a database-related exception."
                ),
                ApplicationErrorKind.GENERIC_ERROR: (
                    "Application logs report a database error."
                ),
            }
        else:
            descriptions = {
                ApplicationErrorKind.CONNECTION_ERROR: (
                    "Application logs report a connection failure."
                ),
                ApplicationErrorKind.TIMEOUT: ("Application logs report a timeout."),
                ApplicationErrorKind.HTTP_5XX: (
                    "Application logs report an HTTP 5xx server error."
                ),
                ApplicationErrorKind.EXCEPTION: (
                    "Application logs report an exception or traceback."
                ),
                ApplicationErrorKind.GENERIC_ERROR: (
                    "Application logs report an application error."
                ),
            }

        return f"{descriptions[classification.kind]} Log message: {message}"
