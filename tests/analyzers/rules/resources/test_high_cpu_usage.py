import pytest

from kubesage.analyzers.rules.resources.high_cpu_usage import HighCPUUsageRule
from kubesage.models.finding import Severity
from kubesage.models.incident import Incident
from kubesage.models.metrics import ContainerMetrics
from kubesage.models.prometheus import PrometheusResourceUsage


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
        containers=[],
        events=[],
        metrics=None,
        prometheus=PrometheusResourceUsage(
            containers=[
                ContainerMetrics(
                    name="app",
                    cpu_usage=0.9,
                    cpu_limit=1,
                ),
            ],
        ),
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
        containers=[],
        events=[],
        metrics=None,
        prometheus=PrometheusResourceUsage(
            containers=[
                ContainerMetrics(
                    name="app",
                    cpu_usage=0.3,
                    cpu_limit=1,
                ),
            ],
        ),
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
        containers=[],
        events=[],
        metrics=None,
        prometheus=PrometheusResourceUsage(
            containers=[
                ContainerMetrics(
                    name="app",
                    cpu_usage=0.3,
                ),
            ],
        ),
    )

    findings = high_cpu_usage_rule.evaluate(incident)

    assert len(findings) == 0
