import re
from dataclasses import dataclass
from enum import StrEnum


class ApplicationErrorKind(StrEnum):
    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    HTTP_5XX = "http_5xx"
    EXCEPTION = "exception"
    GENERIC_ERROR = "generic_error"


class ApplicationErrorDomain(StrEnum):
    DATABASE = "database"


@dataclass(frozen=True)
class ApplicationErrorClassification:
    kind: ApplicationErrorKind
    domain: ApplicationErrorDomain | None = None


class ApplicationErrorClassifier:
    _DATABASE_PATTERN = re.compile(
        r"\b(?:database|db|sql)\b",
        re.IGNORECASE,
    )

    _CONNECTION_PATTERN = re.compile(
        r"\b(?:connection|connect)\b.*"
        r"\b(?:refused|reset|failed|failure|error|unreachable)\b",
        re.IGNORECASE,
    )

    _TIMEOUT_PATTERN = re.compile(
        r"\b(?:timeout|timed\s+out)\b",
        re.IGNORECASE,
    )

    _HTTP_5XX_PATTERN = re.compile(
        r"\bHTTP\s+5\d{2}\b",
        re.IGNORECASE,
    )

    _EXCEPTION_PATTERN = re.compile(
        r"(?:\bexception\b|\b\w+exception\b|\btraceback\b)",
        re.IGNORECASE,
    )

    _ERROR_PATTERN = re.compile(
        r"\berror\b",
        re.IGNORECASE,
    )

    def classify(self, message: str) -> ApplicationErrorClassification | None:
        domain = self._detect_domain(message)

        if self._CONNECTION_PATTERN.search(message):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.CONNECTION_ERROR,
                domain=domain,
            )

        if self._TIMEOUT_PATTERN.search(message):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.TIMEOUT,
                domain=domain,
            )

        if self._HTTP_5XX_PATTERN.search(message):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.HTTP_5XX,
                domain=domain,
            )

        if self._EXCEPTION_PATTERN.search(message):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.EXCEPTION,
                domain=domain,
            )

        if self._ERROR_PATTERN.search(message):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.GENERIC_ERROR,
                domain=domain,
            )

        return None

    def _detect_domain(self, message: str) -> ApplicationErrorDomain | None:
        if self._DATABASE_PATTERN.search(message):
            return ApplicationErrorDomain.DATABASE

        return None
