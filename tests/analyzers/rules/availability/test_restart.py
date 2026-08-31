from datetime import UTC, datetime

from kubesage.analyzers.rules.availability.restart import RestartRule
from kubesage.models.container import ContainerSnapshot
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry, LogSnapshot

LOG_TIMESTAMP = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)


def test_restart_below_threshold_returns_no_finding() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        observed_at=datetime.now(),
        kubernetes_logs=LogSnapshot(source="kubernetes"),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=True,
                restart_count=2,
                waiting_reason=None,
                last_exit_code=0,
                image="python:3.14",
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = RestartRule().evaluate(incident)

    assert len(findings) == 0


def test_restart_above_threshold_returns_finding() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        observed_at=datetime.now(),
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            entries=[LogEntry(LOG_TIMESTAMP, message="connection refused redis")],
        ),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=True,
                restart_count=15,
                waiting_reason=None,
                last_exit_code=1,
                image="python:3.14",
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = RestartRule().evaluate(incident)

    assert len(findings) == 1


def test_restart_equal_threshold_returns_finding() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        observed_at=datetime.now(),
        kubernetes_logs=LogSnapshot(source="kubernetes"),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=True,
                restart_count=5,
                waiting_reason=None,
                last_exit_code=1,
                image="python:3.14",
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = RestartRule().evaluate(incident)

    assert len(findings) == 1


def test_multiple_containers_return_multiple_findings() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        observed_at=datetime.now(),
        kubernetes_logs=LogSnapshot(source="kubernetes"),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=True,
                restart_count=15,
                waiting_reason=None,
                last_exit_code=1,
                image="python:3.14",
            ),
            ContainerSnapshot(
                name="app2",
                ready=True,
                restart_count=15,
                waiting_reason=None,
                last_exit_code=1,
                image="python:3.14",
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = RestartRule().evaluate(incident)

    assert len(findings) == 2


def test_restart_rule_ignores_waiting_reason() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        observed_at=datetime.now(),
        kubernetes_logs=LogSnapshot(source="kubernetes"),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=True,
                restart_count=0,
                waiting_reason=None,
                last_exit_code=None,
                image="python:3.14",
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = RestartRule().evaluate(incident)

    assert len(findings) == 0
