from kubesage.models.ai_context import AIContext
from kubesage.models.container import ContainerSnapshot
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident
from kubesage.models.log import LogSnapshot


def test_root_causes_ignore_caused_findings() -> None:
    child = Finding(
        rule="app_down",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.CRITICAL,
        title="Application unavailable",
        description="Application is down",
        caused_by=["database_failure"],
    )

    root = Finding(
        rule="database_failure",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.HIGH,
        title="Database failure",
        description="Connection pool exhausted",
    )

    context = AIContext(
        incident=Incident(
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
        ),
        findings=[child, root],
    )

    assert context.root_causes == [root]
