from kubesage.analyzers.correlations.rules.cpu_contention import (
    CPUContentionCorrelation,
)
from kubesage.models.finding import Finding, ResourceRef, Severity


def test_finding_has_cpu_contention() -> None:
    findings = [
        Finding(
            severity=Severity.HIGH,
            title="Container is crashing",
            description="Container is crashing",
            resource=ResourceRef(namespace="default", name="demo", kind="Pod"),
            rule="high_cpu_usage",
        ),
        Finding(
            severity=Severity.HIGH,
            title="Container is crashing",
            description="Container is crashing",
            resource=ResourceRef(namespace="default", name="demo", kind="Pod"),
            rule="cpu_throttling",
        ),
    ]

    findings = CPUContentionCorrelation().apply(findings)

    assert len(findings) == 3
    assert findings[2].rule == "CPU contention"


def test_finding_has_no_cpu_contention() -> None:
    findings = [
        Finding(
            severity=Severity.HIGH,
            title="Container is crashing",
            description="Container is crashing",
            resource=ResourceRef(namespace="default", name="demo", kind="Pod"),
            rule="high_cpu_usage",
        ),
    ]

    findings = CPUContentionCorrelation().apply(findings)

    assert len(findings) == 1
