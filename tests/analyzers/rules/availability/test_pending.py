from datetime import datetime

import pytest

from kubesage.analyzers.rules.availability.pending import PendingRule
from kubesage.models.container import ContainerSnapshot
from kubesage.models.event import Event
from kubesage.models.incident import Incident


@pytest.fixture
def rule() -> PendingRule:
    return PendingRule()


@pytest.fixture
def incident_no_event() -> Incident:
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
            ),
        ],
        events=[],
    )


def test_pending_no_event(incident_no_event: Incident, rule: PendingRule) -> None:
    findings = rule.evaluate(incident_no_event)

    assert len(findings) == 0


@pytest.fixture
def incident_pending() -> Incident:
    return Incident(
        namespace="test",
        pod="test",
        phase="Pending",
        containers=[
            ContainerSnapshot(
                name="test",
                image="test",
                ready=True,
                restart_count=0,
            ),
        ],
        events=[
            Event(
                type="Pending",
                reason="FailedScheduling",
                message="The pod is in Pending",
                last_timestamp=datetime.fromisoformat("2022-01-01T00:00:00Z"),
            ),
            Event(
                type="Scheduled",
                reason="Scheduled",
                message="The pod is scheduled",
                last_timestamp=datetime.fromisoformat("2022-01-01T00:00:00Z"),
            ),
        ],
    )


def test_pending_not_ready(incident_pending: Incident, rule: PendingRule) -> None:
    findings = rule.evaluate(incident_pending)

    assert len(findings) == 1
    assert findings[0].structured_evidences[0].name == "phase"
    assert findings[0].structured_evidences[0].value == "Pending"
    assert findings[0].structured_evidences[1].name == "scheduling_failure"
    assert findings[0].structured_evidences[1].value == "The pod is in Pending"
    assert findings[0].recommendations == [
        "Review the scheduler event message.",
        "Check node resources (CPU, memory, ephemeral storage).",
        "Verify node selectors, affinities and tolerations.",
        "Verify PersistentVolumeClaims if applicable.",
    ]
    assert findings[0].metadata == {
        "event_reason": "FailedScheduling",
    }


@pytest.fixture
def incident_running() -> Incident:
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
            ),
        ],
        events=[
            Event(
                type="Running",
                reason="SomethingElse",
                message="The pod is running",
                last_timestamp=datetime.fromisoformat("2022-01-01T00:00:00Z"),
            ),
        ],
    )


def test_incident_other_event(incident_running: Incident, rule: PendingRule) -> None:
    findings = rule.evaluate(incident_running)

    assert len(findings) == 0
