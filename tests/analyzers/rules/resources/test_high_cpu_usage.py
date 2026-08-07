import pytest

from kubesage.analyzers.rules.resources.high_cpu_usage import HighCPUUsageRule
from kubesage.models.container import (
    ContainerResources,
    ContainerSnapshot,
    ContainerUsage,
)
from kubesage.models.evidence import EvidenceType
from kubesage.models.finding import Severity
from kubesage.models.incident import Incident


@pytest.fixture
def high_cpu_usage_rule() -> HighCPUUsageRule:
    return HighCPUUsageRule()


def test_high_cpu_usage_high(high_cpu_usage_rule: HighCPUUsageRule) -> None:
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
                    cpu_usage=0.9,
                ),
                resources=ContainerResources(
                    name="app",
                    cpu_limit=1.0,
                ),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = high_cpu_usage_rule.evaluate(incident)

    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert findings[0].title == "Detect containers close to their CPU limit."
    assert findings[0].description == "Container 'app' is using 90% of its CPU limit."
    assert findings[0].metadata == {
        "container": "app",
        "cpu_usage": 0.9,
        "cpu_limit": 1,
        "usage_ratio": 0.9,
    }
    assert findings[0].confidence == 0.95


def test_high_cpu_usage_low(high_cpu_usage_rule: HighCPUUsageRule) -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        containers=[
            ContainerSnapshot(
                name="demo",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=ContainerUsage(
                    name="demo",
                    cpu_usage=0.3,
                ),
                resources=ContainerResources(
                    name="demo",
                    cpu_limit=1,
                ),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = high_cpu_usage_rule.evaluate(incident)

    assert len(findings) == 0


def _test_cpu_usage_limit_missing(high_cpu_usage_rule: HighCPUUsageRule) -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        containers=[
            ContainerSnapshot(
                name="demo",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=ContainerUsage(
                    name="demo",
                    cpu_usage=0.3,
                ),
                resources=ContainerResources(
                    name="demo",
                ),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    findings = high_cpu_usage_rule.evaluate(incident)

    assert len(findings) == 0


def test_high_cpu_usage_contains_structured_evidence(
    high_cpu_usage_rule: HighCPUUsageRule,
) -> None:
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
                    cpu_usage=0.9,
                ),
                resources=ContainerResources(
                    name="app",
                    cpu_limit=1.0,
                ),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    finding = high_cpu_usage_rule.evaluate(incident)[0]

    assert len(finding.structured_evidences) == 4

    cpu_usage = finding.structured_evidences[0]
    assert cpu_usage.type == EvidenceType.METRIC
    assert cpu_usage.name == "cpu_usage"
    assert cpu_usage.value == "0.9"
    assert cpu_usage.source == "prometheus"
    assert cpu_usage.unit == "cores"
    assert cpu_usage.description is not None

    cpu_limit = finding.structured_evidences[1]
    assert cpu_limit.type == EvidenceType.METRIC
    assert cpu_limit.name == "cpu_limit"
    assert cpu_limit.value == "1.0"
    assert cpu_limit.source == "kubernetes"
    assert cpu_limit.unit == "cores"

    ratio = finding.structured_evidences[2]
    assert ratio.type == EvidenceType.METRIC
    assert ratio.name == "cpu_usage_ratio"
    assert ratio.value == "0.9"
    assert ratio.source == "kubesage"
    assert ratio.unit == "ratio"

    threshold = finding.structured_evidences[3]
    assert threshold.type == EvidenceType.THRESHOLD
    assert threshold.name == "cpu_usage_threshold"
    assert threshold.value == "0.8"
    assert threshold.source == "kubesage"
    assert threshold.unit == "ratio"
