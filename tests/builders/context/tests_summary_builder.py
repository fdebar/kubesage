from kubesage.builders.context.summary_builder import SummaryBuilder
from kubesage.models.finding import Finding, ResourceRef, Severity


def test_summary_without_findings() -> None:
    builder = SummaryBuilder()

    assert builder.build([]) == "No issue detected."


def test_summary_with_findings() -> None:
    builder = SummaryBuilder()

    findings = [
        Finding(
            title="CrashLoopBackOff",
            description="...",
            severity=Severity.CRITICAL,
            confidence=0.86,
            rule="...",
            resource=ResourceRef(
                api_version="v1",
                kind="Pod",
                namespace="default",
                name="test-pod",
            ),
            evidences=["pod is restarting"],
        )
    ]

    summary = builder.build(findings)

    assert "CrashLoopBackOff" in summary
