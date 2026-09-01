from datetime import UTC, datetime

from kubesage.analyzers.rules.application.application_error import (
    ApplicationErrorRule,
)
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry, LogSnapshot, LogSource


def _incident_with_logs(*messages: str) -> Incident:
    entries = [
        LogEntry(
            timestamp=datetime(2026, 8, 31, 8, 0, index, tzinfo=UTC),
            message=message,
            labels={
                "namespace": "default",
                "pod": "my-api",
                "container": "api",
            },
        )
        for index, message in enumerate(messages, start=1)
    ]

    return Incident(
        namespace="default",
        pod="my-api",
        phase="Running",
        observed_at=datetime(2026, 8, 31, 8, 0, tzinfo=UTC),
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=entries,
        ),
    )


def test_detects_error_log() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "INFO request completed",
            "ERROR failed to process request",
        )
    )

    assert len(findings) == 1
    assert findings[0].rule == "application_error"
    assert findings[0].severity.value == "ERROR"
    assert findings[0].structured_evidences[0].value == (
        "ERROR failed to process request"
    )


def test_detects_traceback() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "Traceback (most recent call last):",
        )
    )

    assert len(findings) == 1


def test_detects_exception_keyword() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "RuntimeException: invalid configuration",
        )
    )

    assert len(findings) == 1


def test_detects_http_5xx() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "request completed with HTTP 500",
            "request completed with HTTP 200",
        )
    )

    assert len(findings) == 1


def test_detects_connection_refused() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "connect to database: connection refused",
        )
    )

    assert len(findings) == 1


def test_detects_timeout() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "database request timeout after 30s",
        )
    )

    assert len(findings) == 1


def test_ignores_normal_logs() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "INFO application started",
            "INFO request completed successfully",
            "HTTP 200",
        )
    )

    assert findings == []


def test_ignores_missing_loki_logs() -> None:
    findings = ApplicationErrorRule().evaluate(
        Incident(
            namespace="default",
            pod="my-api",
            phase="Running",
            observed_at=datetime(2026, 8, 31, 8, 0, tzinfo=UTC),
        )
    )

    assert findings == []


def test_classifies_database_error() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "ERROR Database connection refused",
        )
    )

    assert len(findings) == 1
    assert findings[0].metadata["error_kind"] == "connection_error"


def test_classifies_connection_error() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "ERROR connection refused",
        )
    )

    assert len(findings) == 1
    assert findings[0].metadata["error_kind"] == "connection_error"


def test_classifies_timeout() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "request timed out after 30s",
        )
    )

    assert len(findings) == 1
    assert findings[0].metadata["error_kind"] == "timeout"


def test_classifies_http_5xx() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "request failed with HTTP 503",
        )
    )

    assert len(findings) == 1
    assert findings[0].metadata["error_kind"] == "http_5xx"


def test_classifies_exception() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "RuntimeException: invalid configuration",
        )
    )

    assert len(findings) == 1
    assert findings[0].metadata["error_kind"] == "exception"


def test_classifies_generic_error() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "ERROR failed to process request",
        )
    )

    assert len(findings) == 1
    assert findings[0].metadata["error_kind"] == "generic_error"


def test_database_error_takes_precedence_over_connection_and_timeout() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "ERROR Database connection timeout",
        )
    )

    assert len(findings) == 1
    assert findings[0].metadata["error_kind"] == "timeout"


def test_database_error_has_semantic_finding() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "ERROR Database connection refused",
        )
    )

    finding = findings[0]

    assert finding.title == "Database connection failure"
    assert finding.metadata["error_kind"] == "connection_error"
    assert finding.metadata["error_domain"] == "database"
    assert "database connection failure" in finding.description.lower()
    assert "Database connection refused" in finding.description


def test_http_5xx_has_semantic_finding() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "HTTP 503 Service Unavailable",
        )
    )

    finding = findings[0]

    assert finding.title == "HTTP 5xx error"
    assert finding.metadata["error_kind"] == "http_5xx"


def test_exception_has_semantic_finding() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "RuntimeException: invalid configuration",
        )
    )

    finding = findings[0]

    assert finding.title == "Application exception"
    assert finding.metadata["error_kind"] == "exception"
