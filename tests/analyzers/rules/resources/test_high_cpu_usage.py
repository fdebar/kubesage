import pytest

from kubesage.analyzers.rules.resources.high_cpu_usage import HighCPUUsageRule
from kubesage.models.container import ContainerSnapshot
from kubesage.models.finding import Severity
from kubesage.models.incident import Incident
from kubesage.models.resources import ContainerResources
from kubesage.models.usage import ContainerUsage


@pytest.fixture
def high_cpu_usage_rule() -> HighCPUUsageRule:
    return HighCPUUsageRule()


def test_high_cpu_usage_high(
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


def test_high_cpu_usage_low(
    high_cpu_usage_rule: HighCPUUsageRule,
) -> None:
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


def _test_cpu_usage_limit_missing(
    high_cpu_usage_rule: HighCPUUsageRule,
) -> None:
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
