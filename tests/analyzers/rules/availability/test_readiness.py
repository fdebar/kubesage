import pytest

from kubesage.analyzers.rules.availability.readiness import ReadinessRule
from kubesage.models.container import ContainerSnapshot
from kubesage.models.finding import ResourceRef
from kubesage.models.incident import Incident


@pytest.fixture
def rule() -> ReadinessRule:
    return ReadinessRule()


@pytest.fixture
def incident() -> Incident:
    return Incident(
        namespace="test",
        pod="test",
        phase="test",
        containers=[
            ContainerSnapshot(
                name="test",
                image="test",
                ready=True,
                restart_count=0,
            ),
        ],
    )


def test_ready_container_returns_no_finding(
    rule: ReadinessRule, incident: Incident
) -> None:
    findings = rule.evaluate(incident)
    assert findings == []


def test_not_ready_container_returns_finding(
    rule: ReadinessRule, incident: Incident
) -> None:
    incident.containers[0].ready = False
    findings = rule.evaluate(incident)

    assert len(findings) == 1
    assert findings[0].resource == ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace=incident.namespace,
        name=incident.pod,
    )
    assert findings[0].evidences == [
        f"Container '{incident.containers[0].name}' ready = False.",
    ]


def test_multiple_not_ready_containers(rule: ReadinessRule, incident: Incident) -> None:
    incident.containers = [
        ContainerSnapshot(
            name="test1",
            image="test1",
            ready=False,
            restart_count=1,
        ),
        ContainerSnapshot(
            name="test2",
            image="test2",
            ready=False,
            restart_count=1,
        ),
    ]
    findings = rule.evaluate(incident)

    assert len(findings) == 2
    assert findings[0].evidences == [
        f"Container '{incident.containers[0].name}' ready = False.",
    ]
    assert findings[1].evidences == [
        f"Container '{incident.containers[1].name}' ready = False.",
    ]


def test_mixed_ready_and_not_ready(rule: ReadinessRule, incident: Incident) -> None:
    incident.containers = [
        ContainerSnapshot(
            name="test1",
            image="test1",
            ready=True,
            restart_count=0,
        ),
        ContainerSnapshot(
            name="test2",
            image="test2",
            ready=False,
            restart_count=1,
        ),
    ]
    findings = rule.evaluate(incident)

    assert len(findings) == 1
    assert findings[0].evidences == [
        f"Container '{incident.containers[1].name}' ready = False.",
    ]
