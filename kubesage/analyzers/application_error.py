import re
import shlex
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from kubesage.models.application_error import ApplicationErrorKind


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

    _TIMESTAMP_PATTERN = re.compile(
        r"\b\d{4}-\d{2}-\d{2}"
        r"[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?"
        r"(?:Z|[+-]\d{2}:?\d{2})?\b",
    )

    _UUID_PATTERN = re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
        r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
        re.IGNORECASE,
    )

    _REQUEST_ID_PATTERN = re.compile(
        r"\b(?:request[_ -]?id|trace[_ -]?id|span[_ -]?id)" r"\s*[:=]\s*[^\s,]+",
        re.IGNORECASE,
    )

    _IP_PATTERN = re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    )

    _ATTEMPT_PATTERN = re.compile(
        r"\battempt\s*[:=]\s*\d+\b",
        re.IGNORECASE,
    )

    _DURATION_PATTERN = re.compile(
        r"\b\d+(?:\.\d+)?(?:ns|us|µs|ms|s|m|h)\b",
        re.IGNORECASE,
    )

    def classify(self, message: str) -> ApplicationErrorClassification | None:
        structured = self._parse_structured_log(message)

        if structured is not None:
            level = structured.get("level", "").lower()

            if level != "error":
                return None

            signal = " ".join(
                value for key in ("msg", "error") if (value := structured.get(key))
            )

            classification = self._classify_signal(signal)
            if classification is not None:
                return classification

            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.GENERIC_ERROR,
                domain=self._detect_domain(signal),
            )

        return self._classify_signal(message)

    def fingerprint(
        self,
        classification: ApplicationErrorClassification,
        message: str,
    ) -> str:
        structured = self._parse_structured_log(message)

        if structured is not None:
            normalized_parts = [
                structured.get("logger", ""),
                structured.get("msg", ""),
                structured.get("error", ""),
            ]

            normalized = " | ".join(
                self._normalize(part) for part in normalized_parts if part
            )
        else:
            normalized = self._normalize(message)

        raw = "|".join(
            [
                classification.kind.value,
                classification.domain.value if classification.domain else "",
                normalized,
            ]
        )

        return sha256(raw.encode()).hexdigest()[:16]

    def _classify_signal(self, signal: str) -> ApplicationErrorClassification | None:
        domain = self._detect_domain(signal)

        if self._CONNECTION_PATTERN.search(signal):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.CONNECTION_ERROR,
                domain=domain,
            )

        if self._TIMEOUT_PATTERN.search(signal):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.TIMEOUT,
                domain=domain,
            )

        if self._HTTP_5XX_PATTERN.search(signal):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.HTTP_5XX,
                domain=domain,
            )

        if self._EXCEPTION_PATTERN.search(signal):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.EXCEPTION,
                domain=domain,
            )

        if self._ERROR_PATTERN.search(signal):
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.GENERIC_ERROR,
                domain=domain,
            )

        return None

    def _parse_structured_log(self, message: str) -> dict[str, str] | None:
        try:
            fields = dict(
                token.split("=", 1) for token in shlex.split(message) if "=" in token
            )
        except ValueError:
            return None

        if "level" not in fields or "msg" not in fields:
            return None

        return fields

    def _normalize(self, message: str) -> str:
        normalized = message.strip()

        normalized = self._TIMESTAMP_PATTERN.sub("<timestamp>", normalized)
        normalized = self._UUID_PATTERN.sub("<uuid>", normalized)
        normalized = self._REQUEST_ID_PATTERN.sub("<request_id>", normalized)
        normalized = self._IP_PATTERN.sub("<ip>", normalized)
        normalized = self._ATTEMPT_PATTERN.sub("attempt=<attempt>", normalized)
        normalized = self._DURATION_PATTERN.sub("<duration>", normalized)

        normalized = re.sub(r"\s+", " ", normalized)

        return normalized.lower()

    def _detect_domain(self, message: str) -> ApplicationErrorDomain | None:
        if self._DATABASE_PATTERN.search(message):
            return ApplicationErrorDomain.DATABASE

        return None
