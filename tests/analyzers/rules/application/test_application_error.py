from datetime import datetime

from kubesage.analyzers.rules.application.application_error import (
    ApplicationErrorRule,
)
from kubesage.models.application_error import ApplicationErrorKind
from kubesage.models.evidence import EvidenceType
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry, LogSnapshot, LogSource


def _entry(
    message: str,
    timestamp: str,
    labels: dict[str, str] | None = None,
) -> LogEntry:
    return LogEntry(
        timestamp=datetime.fromisoformat(timestamp),
        message=message,
        labels=labels or {},
    )


def _incident_with_logs(*entries: LogEntry) -> Incident:
    return Incident(
        namespace="default",
        pod="application-error-pod",
        phase="Running",
        observed_at=datetime.now(),
        loki_logs=LogSnapshot(
            source=LogSource.LOKI,
            entries=list(entries),
        ),
    )


def test_single_application_error_creates_one_finding() -> None:
    incident = _incident_with_logs(
        _entry(
            "ERROR connection refused",
            "2026-09-03T10:00:00+00:00",
        )
    )

    findings = ApplicationErrorRule().evaluate(incident)

    assert len(findings) == 1
    finding = findings[0]

    assert finding.metadata["occurrences"] == 1
    assert finding.metadata["first_seen"] == "2026-09-03T10:00:00+00:00"
    assert finding.metadata["last_seen"] == "2026-09-03T10:00:00+00:00"
    assert finding.metadata["error_kind"] == ApplicationErrorKind.CONNECTION_ERROR.value


def test_repeated_identical_errors_are_aggregated() -> None:
    incident = _incident_with_logs(
        _entry(
            "ERROR connection refused",
            "2026-09-03T10:00:00+00:00",
        ),
        _entry(
            "ERROR connection refused",
            "2026-09-03T10:01:00+00:00",
        ),
        _entry(
            "ERROR connection refused",
            "2026-09-03T10:02:00+00:00",
        ),
    )

    findings = ApplicationErrorRule().evaluate(incident)

    assert len(findings) == 1
    assert findings[0].metadata["occurrences"] == 3
    assert findings[0].metadata["first_seen"] == "2026-09-03T10:00:00+00:00"
    assert findings[0].metadata["last_seen"] == "2026-09-03T10:02:00+00:00"


def test_different_error_kinds_create_different_findings() -> None:
    incident = _incident_with_logs(
        _entry(
            "ERROR connection refused",
            "2026-09-03T10:00:00+00:00",
        ),
        _entry(
            "ERROR request timed out",
            "2026-09-03T10:01:00+00:00",
        ),
    )

    findings = ApplicationErrorRule().evaluate(incident)
    assert len(findings) == 2


def test_different_error_fingerprints_create_different_findings() -> None:
    incident = _incident_with_logs(
        _entry(
            "ERROR connection refused to postgres:5432",
            "2026-09-03T10:00:00+00:00",
        ),
        _entry(
            "ERROR connection refused to postgres:5432",
            "2026-09-03T10:01:00+00:00",
        ),
        _entry(
            "ERROR connection refused to redis:6379",
            "2026-09-03T10:02:00+00:00",
        ),
    )

    findings = ApplicationErrorRule().evaluate(incident)
    assert len(findings) == 2

    occurrences = sorted(finding.metadata["occurrences"] for finding in findings)
    assert occurrences == [1, 2]


def test_application_error_examples_are_limited() -> None:
    incident = _incident_with_logs(
        _entry(
            "ERROR connection refused attempt=1",
            "2026-09-03T10:00:00+00:00",
        ),
        _entry(
            "ERROR connection refused attempt=2",
            "2026-09-03T10:01:00+00:00",
        ),
        _entry(
            "ERROR connection refused attempt=3",
            "2026-09-03T10:02:00+00:00",
        ),
        _entry(
            "ERROR connection refused attempt=4",
            "2026-09-03T10:03:00+00:00",
        ),
    )

    findings = ApplicationErrorRule().evaluate(incident)
    assert len(findings) == 1

    evidence = findings[0].structured_evidences[0]
    assert len(evidence.metadata["examples"]) == 3


def test_same_error_with_different_request_ids_is_aggregated() -> None:
    incident = _incident_with_logs(
        _entry(
            "ERROR database connection refused request_id=abc123",
            "2026-09-03T10:00:00+00:00",
        ),
        _entry(
            "ERROR database connection refused request_id=def456",
            "2026-09-03T10:01:00+00:00",
        ),
    )

    findings = ApplicationErrorRule().evaluate(incident)

    assert len(findings) == 1
    assert findings[0].metadata["occurrences"] == 2


def test_finding_contains_aggregated_evidence() -> None:
    incident = _incident_with_logs(
        _entry(
            "ERROR connection refused",
            "2026-09-03T10:00:00+00:00",
        ),
        _entry(
            "ERROR connection refused",
            "2026-09-03T10:01:00+00:00",
        ),
    )

    findings = ApplicationErrorRule().evaluate(incident)
    evidence = findings[0].structured_evidences[0]

    assert evidence.type == EvidenceType.LOG
    assert evidence.source == "loki"
    assert evidence.metadata["occurrences"] == 2
    assert evidence.metadata["fingerprint"]


def test_no_application_errors_returns_no_findings() -> None:
    incident = _incident_with_logs(
        _entry(
            "INFO application started successfully",
            "2026-09-03T10:00:00+00:00",
        )
    )

    findings = ApplicationErrorRule().evaluate(incident)

    assert findings == []
