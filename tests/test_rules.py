from analyzers.rules.crashloop import CrashLoopRule
from analyzers.rules.connectivity import ConnectivityRule
from analyzers.rules.oom import OOMRule
from models.container import ContainerInfo
from models.incident import Incident


def test_crashloopbackoff() -> None:

    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        logs="connection refused redis",
        containers=[
            ContainerInfo(
                name="app",
                ready=False,
                restart_count=5,
                waiting_reason="CrashLoopBackOff",
                last_exit_code=1,
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = CrashLoopRule().evaluate(incident)

    assert any("CrashLoopBackOff detected" in f.title for f in findings)


def test_connectivity() -> None:

    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        logs="error: connection refused by server",
        containers=[],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = ConnectivityRule().evaluate(incident)

    assert any("Connection refused" in f.title for f in findings)


def test_oomkilled() -> None:

    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        logs="",
        containers=[
            ContainerInfo(
                name="app",
                ready=False,
                restart_count=1,
                waiting_reason="OOMKilled",
                last_exit_code=137,
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = OOMRule().evaluate(incident)

    assert any("OOMKilled detected" in f.title for f in findings)
