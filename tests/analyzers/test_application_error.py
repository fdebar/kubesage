from datetime import datetime

from kubesage.analyzers.application_error import (
    ApplicationErrorClassifier,
    ApplicationErrorKind,
)
from kubesage.analyzers.rules.application.application_error import ApplicationErrorRule
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry, LogSnapshot


def _incident_with_logs(
    *messages: str,
) -> Incident:
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


def test_database_timeout_has_domain() -> None:
    classification = ApplicationErrorClassifier().classify(
        "database request timed out",
    )

    assert classification is not None
    assert classification.kind == ApplicationErrorKind.TIMEOUT


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
