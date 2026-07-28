from kubesage.analyzers.rules.infrastructure.memory_pressure import MemoryPressureRule
from kubesage.models.incident import Incident
from kubesage.models.kubernetes_snapshot import Event


def test_memory_pressure_detected() -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Running",
        events=[
            Event(
                last_timestamp="2026-01-01T00:00:00Z",
                type="Warning",
                reason="Evicted",
                message=("The node was low on resource: memory"),
            )
        ],
    )

    findings = MemoryPressureRule().evaluate(incident)

    assert len(findings) == 1
    assert findings[0].rule == "Memory Pressure"
