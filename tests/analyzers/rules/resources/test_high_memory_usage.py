from datetime import datetime

import pytest

from kubesage.analyzers.rules.resources.high_memory_usage import HighMemoryUsageRule
from kubesage.models.container import (
    ContainerResources,
    ContainerSnapshot,
    ContainerUsage,
)
from kubesage.models.evidence import EvidenceType
from kubesage.models.finding import Severity
from kubesage.models.incident import Incident
from kubesage.models.log import LogSnapshot


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
        observed_at=datetime.now(),
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[
            ContainerSnapshot(
                name="app",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=ContainerUsage(
                    name="app",
                    memory_usage=1024,
                ),
                resources=ContainerResources(
                    name="app",
                    memory_limit=1280,
                ),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
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
        observed_at=datetime.now(),
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[
            ContainerSnapshot(
                name="app",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=ContainerUsage(
                    name="app",
                    memory_usage=128,
                ),
                resources=ContainerResources(
                    name="app",
                    memory_limit=1280,
                ),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
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
        observed_at=datetime.now(),
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            lines=["connection refused redis"],
        ),
        containers=[
            ContainerSnapshot(
                name="app",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=ContainerUsage(
                    name="app",
                    memory_usage=1024,
                ),
                resources=ContainerResources(
                    name="app",
                ),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )
    findings = high_memory_usage_rule.evaluate(incident)

    assert len(findings) == 0


def test_high_memory_usage_contains_structured_evidence(
    high_memory_usage_rule: HighMemoryUsageRule,
) -> None:
    incident = Incident(
        namespace="default",
        pod="demo",
        phase="Running",
        observed_at=datetime.now(),
        containers=[
            ContainerSnapshot(
                name="app",
                image="python:3.12-slim",
                ready=True,
                restart_count=0,
                usage=ContainerUsage(
                    name="app",
                    memory_usage=1024,
                ),
                resources=ContainerResources(
                    name="app",
                    memory_limit=1280,
                ),
            ),
        ],
        events=[],
        metrics=None,
        prometheus=None,
    )

    finding = high_memory_usage_rule.evaluate(incident)[0]

    assert len(finding.structured_evidences) == 4

    memory_usage = finding.structured_evidences[0]
    assert memory_usage.type == EvidenceType.METRIC
    assert memory_usage.name == "memory_usage"
    assert memory_usage.value == "1024"
    assert memory_usage.source == "prometheus"
    assert memory_usage.unit == "bytes"

    memory_limit = finding.structured_evidences[1]
    assert memory_limit.type == EvidenceType.METRIC
    assert memory_limit.name == "memory_limit"
    assert memory_limit.value == "1280"
    assert memory_limit.source == "kubernetes"
    assert memory_limit.unit == "bytes"

    ratio = finding.structured_evidences[2]
    assert ratio.name == "memory_usage_ratio"
    assert ratio.value == "0.8"
    assert ratio.source == "kubesage"
    assert ratio.unit == "ratio"

    threshold = finding.structured_evidences[3]
    assert threshold.name == "memory_usage_threshold"
    assert threshold.value == "0.8"
    assert threshold.source == "kubesage"
    assert threshold.unit == "ratio"
