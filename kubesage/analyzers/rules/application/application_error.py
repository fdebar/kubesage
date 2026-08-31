import re
from enum import StrEnum

from kubesage.analyzers.rules.base import BaseRule
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


class ApplicationErrorKind(StrEnum):
    DATABASE_ERROR = "database_error"
    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    HTTP_5XX = "http_5xx"
    EXCEPTION = "exception"
    GENERIC_ERROR = "generic_error"


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
            error_kind = self._classify(entry.message)
            if error_kind is None:
                continue

            findings.append(
                Finding(
                    rule=self.rule_id,
                    severity=Severity.ERROR,
                    kind=FindingKind.OBSERVATION,
                    title=self._title(error_kind),
                    description=self._description(error_kind, entry.message),
                    metadata={
                        "error_kind": error_kind.value,
                        "log_timestamp": entry.timestamp.isoformat(),
                    },
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

    def _classify(self, message: str) -> ApplicationErrorKind | None:
        if re.search(
            r"\b(?:database|db|sql)\b.*\b(?:error|failure|failed|refused|timeout)\b",
            message,
            re.IGNORECASE,
        ):
            return ApplicationErrorKind.DATABASE_ERROR

        if re.search(
            r"\bconnection\s+(?:refused|reset|failed|failure|error)\b",
            message,
            re.IGNORECASE,
        ):
            return ApplicationErrorKind.CONNECTION_ERROR

        if re.search(
            r"\b(?:timeout|timed out)\b",
            message,
            re.IGNORECASE,
        ):
            return ApplicationErrorKind.TIMEOUT

        if re.search(
            r"\bHTTP\s+5\d{2}\b",
            message,
            re.IGNORECASE,
        ):
            return ApplicationErrorKind.HTTP_5XX

        if re.search(
            r"(?:\bexception\b|\b\w+exception\b|\btraceback\b)",
            message,
            re.IGNORECASE,
        ):
            return ApplicationErrorKind.EXCEPTION

        if re.search(r"\berror\b", message, re.IGNORECASE):
            return ApplicationErrorKind.GENERIC_ERROR

        return None

    def _title(self, error_kind: ApplicationErrorKind) -> str:
        titles = {
            ApplicationErrorKind.DATABASE_ERROR: "Database connection failure",
            ApplicationErrorKind.CONNECTION_ERROR: "Application connection failure",
            ApplicationErrorKind.TIMEOUT: "Application timeout",
            ApplicationErrorKind.HTTP_5XX: "HTTP 5xx error",
            ApplicationErrorKind.EXCEPTION: "Application exception",
            ApplicationErrorKind.GENERIC_ERROR: "Application error",
        }

        return titles[error_kind]

    def _description(self, error_kind: ApplicationErrorKind, message: str) -> str:
        descriptions = {
            ApplicationErrorKind.DATABASE_ERROR: (
                "Application logs report a database error."
            ),
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

        return f"{descriptions[error_kind]} Log message: {message}"
