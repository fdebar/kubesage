import json
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


@dataclass(frozen=True)
class _ParsedLog:
    fields: dict[str, str]
    signal: str
    level: str | None


class ApplicationErrorClassifier:
    """Parse common application log formats and classify error signals."""

    ERROR_LEVELS = frozenset(
        {"error", "err", "fatal", "critical", "panic", "alert", "emergency"}
    )
    WARNING_LEVELS = frozenset({"warn", "warning"})
    NON_ERROR_LEVELS = frozenset({"info", "debug", "trace"}) | WARNING_LEVELS
    _LEVEL_KEYS = ("level", "severity", "log_level", "loglevel")
    _MESSAGE_KEYS = (
        "msg",
        "message",
        "error",
        "err",
        "exception",
        "reason",
        "detail",
        "http.status_code",
        "status_code",
        "status",
        "exception_type",
        "error_type",
        "error.message",
        "error.type",
        "exception.message",
        "exception.type",
        "code",
    )

    _LEVEL_PREFIX_PATTERN = re.compile(
        r"^\s*(?:\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
        r"(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\s+)?"
        r"(?:\[(?P<bracket_level>fatal|critical|panic|error|err|warning|warn|"
        r"info|debug|trace|alert|emergency)\]|"
        r"(?P<level>fatal|critical|panic|error|err|warning|warn|info|debug|"
        r"trace|alert|emergency))"
        r"(?:\s*[:\-]\s*|\s+|$)",
        re.IGNORECASE,
    )
    _DATABASE_PATTERN = re.compile(
        r"\b(?:database|db|sql|postgres(?:ql)?|mysql|sqlite|mongodb|mongo)\b",
        re.IGNORECASE,
    )
    _CONNECTION_PATTERN = re.compile(
        r"\b(?:connection|connect(?:ion)?)(?:error)?\b.{0,100}"
        r"\b(?:refused|reset|failed|failure|error|unreachable|closed|lost)\b"
        r"|\b(?:could not|cannot|unable to|failed to)\s+connect\b"
        r"|\b(?:ECONNREFUSED|ECONNRESET|EHOSTUNREACH|ENETUNREACH)\b",
        re.IGNORECASE,
    )
    _TIMEOUT_PATTERN = re.compile(
        r"\b(?:timeout|timed\s+out|deadline\s+exceeded)\b",
        re.IGNORECASE,
    )
    _HTTP_5XX_PATTERN = re.compile(
        r"\b(?:HTTP(?:/\d(?:\.\d)?)?\s*[:=]?\s*|status(?:[_ ]code)?\s*[:=]?\s*)"
        r"5\d{2}\b|\b5\d{2}\s+(?:internal\s+server|bad\s+gateway|"
        r"service\s+unavailable|gateway\s+timeout)\b",
        re.IGNORECASE,
    )
    _EXCEPTION_PATTERN = re.compile(
        r"(?:\b\w*exception\b|\btraceback\b|\bstack\s+trace\b|\bcaused\s+by:)",
        re.IGNORECASE,
    )
    _ERROR_PATTERN = re.compile(r"\b(?:error|failure|failed)\b", re.IGNORECASE)

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
    _IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    _ATTEMPT_PATTERN = re.compile(r"\battempt\s*[:=]\s*\d+\b", re.IGNORECASE)
    _DURATION_PATTERN = re.compile(
        r"\b\d+(?:\.\d+)?(?:ns|us|µs|ms|s|m|h)\b", re.IGNORECASE
    )

    def classify(self, message: str) -> ApplicationErrorClassification | None:
        parsed = self._parse(message)

        if parsed.level in self.NON_ERROR_LEVELS:
            return None

        if parsed.level is not None and parsed.level not in self.ERROR_LEVELS:
            # Unknown explicit levels should not be treated as application errors.
            return None

        classification = self._classify_signal(parsed.signal)
        if classification is not None:
            return classification

        if parsed.level in self.ERROR_LEVELS:
            return ApplicationErrorClassification(
                kind=ApplicationErrorKind.GENERIC_ERROR,
                domain=self._detect_domain(parsed.signal),
            )

        return None

    def log_level(self, message: str) -> str | None:
        """Return a normalized level from structured logs or plain-text prefixes."""

        return self._parse(message).level

    def structured_level(self, message: str) -> str | None:
        """Backward-compatible alias for callers using the former method name."""

        return self.log_level(message)

    def fingerprint(
        self,
        classification: ApplicationErrorClassification,
        message: str,
    ) -> str:
        parsed = self._parse(message)
        logger = parsed.fields.get("logger") or parsed.fields.get("service") or ""
        normalized = " | ".join(
            part
            for part in (self._normalize(logger), self._normalize(parsed.signal))
            if part
        )

        raw = "|".join(
            (
                classification.kind.value,
                classification.domain.value if classification.domain else "",
                normalized,
            )
        )
        return sha256(raw.encode()).hexdigest()[:16]

    def _parse(self, message: str) -> _ParsedLog:
        structured = self._parse_json(message)
        if structured is None:
            structured = self._parse_logfmt(message)

        if structured is not None:
            fields = structured
            signal = " ".join(
                (
                    f"{key}={fields[key]}"
                    if key in {"http.status_code", "status_code", "status"}
                    else fields[key]
                )
                for key in self._MESSAGE_KEYS
                if fields.get(key, "").strip()
            )
            # Include common structured exception details when they use other keys.
            if not signal:
                signal = " ".join(
                    value
                    for key, value in fields.items()
                    if key not in self._LEVEL_KEYS and key not in {"logger", "service"}
                )
            return _ParsedLog(
                fields=fields,
                signal=signal,
                level=self._field_level(fields),
            )

        prefix = self._LEVEL_PREFIX_PATTERN.match(message)
        if prefix is not None:
            level = (prefix.group("level") or prefix.group("bracket_level")).lower()
            signal = message[prefix.end() :].strip()
            return _ParsedLog({}, signal, level)

        return _ParsedLog({}, message, None)

    def _parse_json(self, message: str) -> dict[str, str] | None:
        try:
            value = json.loads(message)
        except json.JSONDecodeError, TypeError:
            return None

        if not isinstance(value, dict):
            return None

        fields: dict[str, str] = {}
        self._flatten_json(value, fields)
        recognized = (*self._LEVEL_KEYS, *self._MESSAGE_KEYS)
        return fields if any(key in fields for key in recognized) else None

    def _parse_logfmt(self, message: str) -> dict[str, str] | None:
        try:
            tokens = shlex.split(message)
        except ValueError:
            return None

        fields: dict[str, str] = {}
        for token in tokens:
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            fields[key.lower()] = value

        recognized = (*self._LEVEL_KEYS, *self._MESSAGE_KEYS)
        return fields if any(key in fields for key in recognized) else None

    @staticmethod
    def _string_value(value: object) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True, ensure_ascii=False)
        return str(value)

    @classmethod
    def _flatten_json(
        cls,
        value: dict[str, object],
        fields: dict[str, str],
        prefix: str = "",
    ) -> None:
        for key, item in value.items():
            if item is None:
                continue
            normalized_key = str(key).lower()
            path = f"{prefix}.{normalized_key}" if prefix else normalized_key
            if isinstance(item, dict):
                cls._flatten_json(item, fields, path)
            else:
                fields[path] = cls._string_value(item)

    @classmethod
    def _field_level(cls, fields: dict[str, str]) -> str | None:
        for key in cls._LEVEL_KEYS:
            if value := fields.get(key, "").strip().lower():
                return value
        return None

    def _classify_signal(self, signal: str) -> ApplicationErrorClassification | None:
        domain = self._detect_domain(signal)

        if self._CONNECTION_PATTERN.search(signal):
            kind = ApplicationErrorKind.CONNECTION_ERROR
        elif self._TIMEOUT_PATTERN.search(signal):
            kind = ApplicationErrorKind.TIMEOUT
        elif self._HTTP_5XX_PATTERN.search(signal):
            kind = ApplicationErrorKind.HTTP_5XX
        elif self._EXCEPTION_PATTERN.search(signal):
            kind = ApplicationErrorKind.EXCEPTION
        elif self._ERROR_PATTERN.search(signal):
            kind = ApplicationErrorKind.GENERIC_ERROR
        else:
            return None

        return ApplicationErrorClassification(kind=kind, domain=domain)

    def _normalize(self, message: str) -> str:
        normalized = message.strip()
        normalized = self._TIMESTAMP_PATTERN.sub("<timestamp>", normalized)
        normalized = self._UUID_PATTERN.sub("<uuid>", normalized)
        normalized = self._REQUEST_ID_PATTERN.sub("<request_id>", normalized)
        normalized = self._IP_PATTERN.sub("<ip>", normalized)
        normalized = self._ATTEMPT_PATTERN.sub("attempt=<attempt>", normalized)
        normalized = self._DURATION_PATTERN.sub("<duration>", normalized)

        return re.sub(r"\s+", " ", normalized).lower()

    def _detect_domain(self, message: str) -> ApplicationErrorDomain | None:
        if self._DATABASE_PATTERN.search(message):
            return ApplicationErrorDomain.DATABASE
        return None
