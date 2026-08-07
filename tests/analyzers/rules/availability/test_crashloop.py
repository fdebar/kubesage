from kubesage.analyzers.rules.availability.crashloop import CrashLoopRule
from kubesage.models.container import ContainerSnapshot
from kubesage.models.evidence import EvidenceType
from kubesage.models.incident import Incident
from kubesage.models.log import LogSnapshot


def make_crashloop_incident() -> Incident:
    return Incident(
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


def test_crashloop_finding_contains_structured_evidence() -> None:
    findings = CrashLoopRule().evaluate(make_crashloop_incident())

    assert len(findings) == 1

    finding = findings[0]

    assert len(finding.structured_evidences) == 3

    waiting_reason = next(
        evidence
        for evidence in finding.structured_evidences
        if evidence.name == "waiting_reason"
    )

    assert waiting_reason.type == EvidenceType.CONTAINER_STATE
    assert waiting_reason.value == "CrashLoopBackOff"
    assert waiting_reason.source == "kubernetes"
    assert waiting_reason.description is not None
    assert "restarting" in waiting_reason.description

    restart_count = next(
        evidence
        for evidence in finding.structured_evidences
        if evidence.name == "restart_count"
    )

    assert restart_count.value == "5"
    assert restart_count.description == "The container has restarted 5 times."

    exit_code = next(
        evidence
        for evidence in finding.structured_evidences
        if evidence.name == "last_exit_code"
    )

    assert exit_code.value == "1"
    assert exit_code.description == (
        "The container's last termination exited with code 1."
    )


def test_crashloop_without_exit_code_omits_exit_code_evidence() -> None:
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
                last_exit_code=None,
                image="python:3.14",
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = CrashLoopRule().evaluate(incident)

    assert len(findings) == 1

    assert not any(
        evidence.name == "last_exit_code"
        for evidence in findings[0].structured_evidences
    )


def test_crashloop_container_returns_finding() -> None:
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
