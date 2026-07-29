from datetime import datetime

from kubesage.analyzers.rules.infrastructure.memory_pressure import MemoryPressureRule
from kubesage.models.finding import FindingKind, Severity
from kubesage.models.incident import Incident
from kubesage.models.kubernetes_snapshot import Event


def test_memory_pressure_detected() -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Running",
        events=[
            Event(
                last_timestamp=datetime.fromisoformat("2026-01-01T00:00:00Z"),
                type="Warning",
                reason="Evicted",
                message=("The node was low on resource: memory"),
            )
        ],
    )

    findings = MemoryPressureRule().evaluate(incident)

    assert len(findings) == 1
    assert findings[0].rule == "Memory Pressure Eviction"
    assert findings[0].severity == Severity.HIGH
    assert findings[0].kind == FindingKind.OBSERVATION
    assert len(findings[0].structured_evidences) == 1
    assert findings[0].structured_evidences[0].name == "eviction_reason"
    assert (
        findings[0].structured_evidences[0].value
        == "The node was low on resource: memory"
    )
    assert findings[0].structured_evidences[0].source == "kubernetes"
    assert findings[0].structured_evidences[0].metadata == {"reason": "Evicted"}
