from datetime import datetime

import pytest

from kubesage.analyzers.rules.availability.oom_killed import OOMKilledRule
from kubesage.models.container import ContainerSnapshot
from kubesage.models.evidence import EvidenceType
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
        observed_at=datetime.now(),
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
        observed_at=datetime.now(),
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


def test_oom_killed(
    incident_oom: Incident,
    rule: OOMKilledRule,
) -> None:
    findings = rule.evaluate(incident_oom)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.structured_evidences[0].name == "last_exit_reason"
    assert finding.structured_evidences[0].value == "OOMKilled"
    assert finding.structured_evidences[0].type == EvidenceType.CONTAINER_STATE
    assert finding.structured_evidences[0].source == "kubernetes"
    assert finding.structured_evidences[0].description == (
        "The previous container execution was terminated "
        "because of an out-of-memory condition."
    )
    assert finding.structured_evidences[1].name == "restart_count"
    assert finding.structured_evidences[1].value == "1"
    assert finding.structured_evidences[1].type == EvidenceType.CONTAINER_STATE
    assert finding.structured_evidences[1].source == "kubernetes"
    assert finding.structured_evidences[1].description == (
        "The container has restarted 1 time."
    )
    assert finding.recommendations == [
        "Review the container memory usage.",
        "Increase the memory limit if appropriate.",
        "Inspect the application for memory leaks.",
    ]
    assert finding.metadata == {"container": "test"}


def test_multiple_oom_killed_containers_return_multiple_findings(
    rule: OOMKilledRule,
) -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Running",
        observed_at=datetime.now(),
        containers=[
            ContainerSnapshot(
                name="app",
                image="app:1",
                ready=True,
                restart_count=3,
                last_exit_reason="OOMKilled",
            ),
            ContainerSnapshot(
                name="worker",
                image="worker:1",
                ready=True,
                restart_count=2,
                last_exit_reason="OOMKilled",
            ),
        ],
    )

    findings = rule.evaluate(incident)

    assert len(findings) == 2
    assert findings[0].metadata == {"container": "app"}
    assert findings[1].metadata == {"container": "worker"}
