from kubesage.analyzers.rules.availability.crashloop import CrashLoopRule
from kubesage.models.container import ContainerSnapshot
from kubesage.models.incident import Incident
from kubesage.models.log import LogSnapshot


def test_running_container_returns_no_findings() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=False,
                restart_count=5,
                waiting_reason="CrashLoopBackOff",
                last_exit_code=1,
                image="python:3.14",
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = CrashLoopRule().evaluate(incident)

    assert any("Container is crashing" in f.title for f in findings)


def test_crashloop_returns_one_finding() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=False,
                restart_count=5,
                waiting_reason="CrashLoopBackOff",
                last_exit_code=1,
                image="python:3.14",
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = CrashLoopRule().evaluate(incident)

    assert len(findings) == 1


def test_multiple_crashloops_return_multiple_findings() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=False,
                restart_count=5,
                waiting_reason="CrashLoopBackOff",
                last_exit_code=1,
                image="python:3.14",
            ),
            ContainerSnapshot(
                name="app2",
                ready=False,
                restart_count=5,
                waiting_reason="CrashLoopBackOff",
                last_exit_code=1,
                image="python:3.14",
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = CrashLoopRule().evaluate(incident)

    assert len(findings) == 2


def test_container_without_waiting_state() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=False,
                restart_count=5,
                waiting_reason=None,
                last_exit_code=None,
                image="python:3.14",
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = CrashLoopRule().evaluate(incident)

    assert len(findings) == 0


def test_container_waiting_for_creation_is_ignored() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[
            ContainerSnapshot(
                name="app",
                ready=False,
                restart_count=0,
                waiting_reason="ContainerCreating",
                last_exit_code=None,
                image="python:3.14",
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = CrashLoopRule().evaluate(incident)

    assert len(findings) == 0
