from kubesage.models.finding import Finding, ResourceRef, Severity
from kubesage.services.findings_correlator import FindingsCorrelator


def test_correlator_memory_exhaustion() -> None:
    correlator = FindingsCorrelator()
    findings = [
        Finding(
            rule="high_memory_usage",
            severity=Severity.WARNING,
            title="High memory usage",
            description="High memory usage",
            resource=ResourceRef(kind="Pod", name="test", namespace="test"),
        ),
        Finding(
            rule="oom_killed",
            severity=Severity.CRITICAL,
            title="OOMKilled",
            description="OOMKilled",
            resource=ResourceRef(kind="Pod", name="test", namespace="test"),
        ),
    ]
    findings = correlator.correlate(findings)

    assert len(findings) == 3


def test_correlator_no_oom_killed() -> None:
    correlator = FindingsCorrelator()
    findings = [
        Finding(
            rule="high_memory_usage",
            severity=Severity.WARNING,
            title="High memory usage",
            description="High memory usage",
            resource=ResourceRef(kind="Pod", name="test", namespace="test"),
        ),
    ]
    findings = correlator.correlate(findings)

    assert len(findings) == 1


def test_correlator_cpu_contention() -> None:
    correlator = FindingsCorrelator()
    findings = [
        Finding(
            rule="high_cpu_usage",
            severity=Severity.WARNING,
            title="High CPU usage",
            description="High CPU usage",
            resource=ResourceRef(kind="Pod", name="test", namespace="test"),
        ),
        Finding(
            rule="cpu_throttling",
            severity=Severity.CRITICAL,
            title="CPU throttling",
            description="CPU throttling",
            resource=ResourceRef(kind="Pod", name="test", namespace="test"),
        ),
    ]
    findings = correlator.correlate(findings)

    assert len(findings) == 3


def test_correlator_no_cpu_throttling() -> None:
    correlator = FindingsCorrelator()
    findings = [
        Finding(
            rule="high_cpu_usage",
            severity=Severity.WARNING,
            title="High CPU usage",
            description="High CPU usage",
            resource=ResourceRef(kind="Pod", name="test", namespace="test"),
        ),
        Finding(
            rule="high_memory_usage",
            severity=Severity.WARNING,
            title="High memory usage",
            description="High memory usage",
            resource=ResourceRef(kind="Pod", name="test", namespace="test"),
        ),
    ]
    findings = correlator.correlate(findings)

    assert len(findings) == 2
