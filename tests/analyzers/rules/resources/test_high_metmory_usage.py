import pytest

from kubesage.analyzers.rules.resources.high_memory_usage import HighMemoryUsageRule
from kubesage.models.finding import Severity
from kubesage.models.incident import Incident
from kubesage.models.log import LogSnapshot
from kubesage.models.metrics import ContainerMetrics
from kubesage.models.prometheus import PrometheusResourceUsage


@pytest.fixture
def high_memory_usage_rule() -> HighMemoryUsageRule:
    return HighMemoryUsageRule()


def test_high_memory_usage_detected(
    high_memory_usage_rule: HighMemoryUsageRule,
) -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[],
        events=[],
        metrics=None,
        prometheus=PrometheusResourceUsage(
            containers=[
                ContainerMetrics(
                    name="app",
                    cpu_usage=0.5,
                    cpu_limit=1,
                    memory_usage=1024,
                    memory_limit=1280,
                ),
            ],
        ),
    )
    findings = high_memory_usage_rule.evaluate(incident)
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert findings[0].title == "Detect containers close to their memory limit."
    assert (
        findings[0].description == "Container 'app' is using 80% of its memory limit."
    )
    assert findings[0].metadata == {
        "container": "app",
        "memory_usage": 1024,
        "memory_limit": 1280,
        "usage_ratio": 0.8,
    }
    assert findings[0].confidence == 0.95


def test_high_memory_usage_below_threshold(
    high_memory_usage_rule: HighMemoryUsageRule,
) -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[],
        events=[],
        metrics=None,
        prometheus=PrometheusResourceUsage(
            containers=[
                ContainerMetrics(
                    name="app",
                    cpu_usage=0.5,
                    cpu_limit=1,
                    memory_usage=128,
                    memory_limit=1280,
                ),
            ],
        ),
    )
    findings = high_memory_usage_rule.evaluate(incident)

    assert len(findings) == 0


def test_missing_memory_limit_is_ignored(
    high_memory_usage_rule: HighMemoryUsageRule,
) -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[],
        events=[],
        metrics=None,
        prometheus=PrometheusResourceUsage(
            containers=[
                ContainerMetrics(
                    name="app",
                    cpu_usage=0.5,
                    cpu_limit=1,
                    memory_usage=1024,
                    memory_limit=None,
                ),
            ],
        ),
    )
    findings = high_memory_usage_rule.evaluate(incident)

    assert len(findings) == 0
