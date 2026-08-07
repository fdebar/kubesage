from kubesage.analyzers.rules.resources.cpu_throttling import CPUThrottlingRule
from kubesage.models.container import ContainerSnapshot, ContainerUsage
from kubesage.models.evidence import EvidenceType
from kubesage.models.finding import FindingKind, Severity
from kubesage.models.incident import Incident


def make_incident(throttling_ratio: float | None) -> Incident:
    return Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        containers=[
            ContainerSnapshot(
                name="app",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=ContainerUsage(
                    name="app",
                    cpu_throttling_ratio=throttling_ratio,
                ),
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )


def test_cpu_throttling_detected() -> None:
    findings = CPUThrottlingRule().evaluate(make_incident(0.35))

    assert len(findings) == 1

    finding = findings[0]

    assert finding.rule == "cpu_throttling"
    assert finding.severity == Severity.WARNING
    assert finding.kind == FindingKind.OBSERVATION
    assert finding.title == "Detect significant CPU throttling"
    assert finding.description == (
        "Container 'app' is experiencing 35% CPU throttling."
    )
    assert finding.confidence == 0.95
    assert finding.metadata == {
        "container": "app",
        "cpu_throttling_ratio": 0.35,
    }


def test_cpu_throttling_contains_structured_evidence() -> None:
    findings = CPUThrottlingRule().evaluate(make_incident(0.35))

    evidences = findings[0].structured_evidences

    assert len(evidences) == 2

    ratio = evidences[0]
    assert ratio.type == EvidenceType.METRIC
    assert ratio.name == "cpu_throttling_ratio"
    assert ratio.value == "0.35"
    assert ratio.source == "prometheus"
    assert ratio.unit == "ratio"
    assert ratio.metadata == {"container": "app"}
    assert ratio.description == ("35% of the container's CPU time is being throttled.")

    threshold = evidences[1]
    assert threshold.type == EvidenceType.THRESHOLD
    assert threshold.name == "cpu_throttling_threshold"
    assert threshold.value == "0.2"
    assert threshold.source == "kubesage"
    assert threshold.unit == "ratio"


def test_cpu_throttling_below_threshold_is_ignored() -> None:
    findings = CPUThrottlingRule().evaluate(make_incident(0.10))

    assert len(findings) == 0


def test_cpu_throttling_at_threshold_is_detected() -> None:
    findings = CPUThrottlingRule().evaluate(make_incident(0.20))

    assert len(findings) == 1


def test_cpu_throttling_missing_usage_is_ignored() -> None:
    findings = CPUThrottlingRule().evaluate(make_incident(None))

    assert len(findings) == 0


def test_cpu_throttling_missing_container_usage_is_ignored() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        containers=[
            ContainerSnapshot(
                name="app",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=None,
            )
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = CPUThrottlingRule().evaluate(incident)

    assert len(findings) == 0


def test_multiple_throttled_containers_return_multiple_findings() -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        containers=[
            ContainerSnapshot(
                name="app",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=ContainerUsage(
                    name="app",
                    cpu_throttling_ratio=0.30,
                ),
            ),
            ContainerSnapshot(
                name="worker",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=ContainerUsage(
                    name="worker",
                    cpu_throttling_ratio=0.40,
                ),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = CPUThrottlingRule().evaluate(incident)

    assert len(findings) == 2
    assert findings[0].metadata["container"] == "app"
    assert findings[1].metadata["container"] == "worker"
