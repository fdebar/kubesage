from kubesage.analyzers.correlations.rules.memory_exhaustion import (
    MemoryExhaustionCorrelation,
)
from kubesage.models.finding import Finding, ResourceRef, Severity


def test_finding_has_memory_contention() -> None:
    findings = [
        Finding(
            severity=Severity.HIGH,
            title="Container is crashing",
            description="Container is crashing",
            resource=ResourceRef(namespace="default", name="demo", kind="Pod"),
            rule="high_memory_usage",
        ),
        Finding(
            severity=Severity.HIGH,
            title="Container is crashing",
            description="Container is crashing",
            resource=ResourceRef(namespace="default", name="demo", kind="Pod"),
            rule="oom_killed",
        ),
    ]

    findings = MemoryExhaustionCorrelation().apply(findings)

    assert len(findings) == 3
    assert findings[2].rule == "Memory exhaustion"


def test_finding_has_no_memory_contention() -> None:
    findings = [
        Finding(
            severity=Severity.HIGH,
            title="Container is crashing",
            description="Container is crashing",
            resource=ResourceRef(namespace="default", name="demo", kind="Pod"),
            rule="memory_throttling",
        ),
    ]

    findings = MemoryExhaustionCorrelation().apply(findings)

    assert len(findings) == 1
