import pytest

from kubesage.analyzers.rules.availability.oom_killed import OOMKilledRule
from kubesage.models.container import ContainerSnapshot
from kubesage.models.incident import Incident


@pytest.fixture
def rule() -> OOMKilledRule:
    return OOMKilledRule()


@pytest.fixture
def incident_no_oom() -> Incident:
    return Incident(
        namespace="test",
        pod="test",
        phase="Running",
        containers=[
            ContainerSnapshot(
                name="test",
                image="test",
                ready=True,
                restart_count=0,
                last_exit_reason=None,
            ),
        ],
    )


def test_oom_killed_no_oom(incident_no_oom: Incident, rule: OOMKilledRule) -> None:
    findings = rule.evaluate(incident_no_oom)

    assert len(findings) == 0


@pytest.fixture
def incident_oom() -> Incident:
    return Incident(
        namespace="test",
        pod="test",
        phase="Running",
        containers=[
            ContainerSnapshot(
                name="test",
                image="test",
                ready=True,
                restart_count=1,
                last_exit_reason="OOMKilled",
            ),
        ],
    )


def test_oom_killed(incident_oom: Incident, rule: OOMKilledRule) -> None:
    findings = rule.evaluate(incident_oom)

    assert len(findings) == 1
    assert findings[0].evidences == [
        "Container 'test' last exit reason = OOMKilled.",
        "Restart count = 1",
    ]
    assert findings[0].recommendations == [
        "Review the container memory usage.",
        "Increase the memory limit if appropriate.",
        "Inspect the application for memory leaks.",
    ]
    assert findings[0].metadata == {
        "container": "test",
        "last_exit_reason": "OOMKilled",
        "restart_count": 1,
    }
