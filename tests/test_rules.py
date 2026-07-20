from analyzers.rules import analyze_incident
from models.container import ContainerInfo
from models.incident import Incident


def test_crashloopbackoff():

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
    )

    findings = analyze_incident(incident)

    assert any(
        "CrashLoopBackOff" in f
        for f in findings
    )