from datetime import datetime

import pytest

from kubesage.analyzers.application_error import (
    ApplicationErrorClassifier,
    ApplicationErrorKind,
)
from kubesage.analyzers.rules.application.application_error import ApplicationErrorRule
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry, LogSnapshot


def _incident_with_logs(*messages: str) -> Incident:
    return Incident(
        namespace="default",
        pod="application-error-pod",
        phase="Running",
        observed_at=datetime.now(),
        loki_logs=LogSnapshot(
            source="loki",
            entries=[
                LogEntry(timestamp=datetime.now(), message=message)
                for message in messages
            ],
        ),
    )


def test_database_connection_error_has_domain() -> None:
    classification = ApplicationErrorClassifier().classify(
        "ERROR Database connection refused",
    )

    assert classification is not None
    assert classification.kind == ApplicationErrorKind.CONNECTION_ERROR
    assert classification.domain is not None
    assert classification.domain.value == "database"


def test_database_timeout_has_domain() -> None:
    classification = ApplicationErrorClassifier().classify(
        "database request timed out",
    )

    assert classification is not None
    assert classification.kind == ApplicationErrorKind.TIMEOUT
    assert classification.domain is not None
    assert classification.domain.value == "database"


def test_connection_error_without_domain() -> None:
    classification = ApplicationErrorClassifier().classify(
        "ERROR connection refused",
    )

    assert classification is not None
    assert classification.kind == ApplicationErrorKind.CONNECTION_ERROR


def test_database_connection_error_exposes_domain() -> None:
    findings = ApplicationErrorRule().evaluate(
        _incident_with_logs(
            "ERROR Database connection refused",
        )
    )
    finding = findings[0]

    assert finding.metadata["error_kind"] == "connection_error"
    assert finding.metadata["error_domain"] == "database"


@pytest.mark.parametrize(
    ("message", "expected_kind"),
    [
        ("ERROR connection refused", ApplicationErrorKind.CONNECTION_ERROR),
        ("unable to connect to upstream", ApplicationErrorKind.CONNECTION_ERROR),
        ("dial tcp: ECONNRESET", ApplicationErrorKind.CONNECTION_ERROR),
        ("request timeout", ApplicationErrorKind.TIMEOUT),
        ("context deadline exceeded", ApplicationErrorKind.TIMEOUT),
        ("HTTP/1.1 503", ApplicationErrorKind.HTTP_5XX),
        ("status_code=502", ApplicationErrorKind.HTTP_5XX),
        ("503 Service Unavailable", ApplicationErrorKind.HTTP_5XX),
        ("Traceback (most recent call last)", ApplicationErrorKind.EXCEPTION),
        ("Caused by: ValueError", ApplicationErrorKind.EXCEPTION),
        ("operation failed", ApplicationErrorKind.GENERIC_ERROR),
    ],
)
def test_plain_text_signals_are_classified(
    message: str,
    expected_kind: ApplicationErrorKind,
) -> None:
    classification = ApplicationErrorClassifier().classify(message)

    assert classification is not None
    assert classification.kind == expected_kind


@pytest.mark.parametrize(
    "message",
    [
        '{"severity":"ERROR","message":"database connection refused"}',
        '{"LEVEL":"error","msg":"database connection refused"}',
        'severity=ERROR message="database connection refused"',
        'log_level=error msg="database connection refused"',
    ],
)
def test_json_and_logfmt_aliases_are_parsed(message: str) -> None:
    classification = ApplicationErrorClassifier().classify(message)

    assert classification is not None
    assert classification.kind == ApplicationErrorKind.CONNECTION_ERROR
    assert classification.domain is not None
    assert classification.domain.value == "database"


@pytest.mark.parametrize(
    ("message", "expected_kind"),
    [
        (
            '{"level":"error","error":{"message":"database timed out"}}',
            ApplicationErrorKind.TIMEOUT,
        ),
        (
            '{"level":"error","http":{"status_code":503}}',
            ApplicationErrorKind.HTTP_5XX,
        ),
        (
            'level=panic msg="worker crashed"',
            ApplicationErrorKind.GENERIC_ERROR,
        ),
        (
            'level=critical exception="ConnectionError: reset by peer"',
            ApplicationErrorKind.CONNECTION_ERROR,
        ),
    ],
)
def test_structured_signals_and_nested_fields_are_classified(
    message: str,
    expected_kind: ApplicationErrorKind,
) -> None:
    classification = ApplicationErrorClassifier().classify(message)

    assert classification is not None
    assert classification.kind == expected_kind


@pytest.mark.parametrize(
    ("message", "expected_level"),
    [
        ('{"level":"FATAL","msg":"crashed"}', "fatal"),
        ('severity=WARNING msg="retrying"', "warning"),
        ("[ERROR] request failed", "error"),
        ("2026-09-25T12:30:00Z WARN retrying", "warn"),
        ("INFO application started", "info"),
    ],
)
def test_log_level_is_normalized_for_structured_and_plain_logs(
    message: str,
    expected_level: str,
) -> None:
    classifier = ApplicationErrorClassifier()

    assert classifier.log_level(message) == expected_level
    assert classifier.structured_level(message) == expected_level


@pytest.mark.parametrize(
    "message",
    [
        '{"level":"warning","msg":"database connection refused"}',
        'severity=info msg="request failed" error="database timeout"',
        '{"level":"notice","message":"operation failed"}',
    ],
)
def test_non_error_or_unknown_explicit_level_is_ignored(message: str) -> None:
    assert ApplicationErrorClassifier().classify(message) is None


def test_error_level_without_recognized_signal_becomes_generic_error() -> None:
    classification = ApplicationErrorClassifier().classify(
        '{"level":"emergency","message":"worker stopped"}'
    )

    assert classification is not None
    assert classification.kind == ApplicationErrorKind.GENERIC_ERROR


def test_unstructured_line_without_error_signal_is_ignored() -> None:
    assert ApplicationErrorClassifier().classify("application started") is None


def test_fingerprint_normalizes_variable_request_data() -> None:
    classifier = ApplicationErrorClassifier()
    first = "ERROR request failed request_id=abc attempt=1 duration=12ms 10.0.0.1"
    second = "ERROR request failed request_id=xyz attempt=9 duration=44ms 10.0.0.2"
    classification = classifier.classify(first)

    assert classification is not None
    assert classifier.fingerprint(classification, first) == classifier.fingerprint(
        classification,
        second,
    )


def test_fingerprint_keeps_distinct_error_messages_separate() -> None:
    classifier = ApplicationErrorClassifier()
    first = "ERROR connection refused to payments"
    second = "ERROR connection refused to inventory"
    classification = classifier.classify(first)

    assert classification is not None
    assert classifier.fingerprint(classification, first) != classifier.fingerprint(
        classification,
        second,
    )
