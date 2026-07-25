from kubesage.builders.context.summary_builder import SummaryBuilder
from kubesage.models.finding import Finding, Severity


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
            source="k8s-events",
            category="Stability",
            evidence=["pod is restarting"],
        )
    ]

    summary = builder.build(findings)

    assert "CrashLoopBackOff" in summary
