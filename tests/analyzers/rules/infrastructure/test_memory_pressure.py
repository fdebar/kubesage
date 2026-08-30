from datetime import datetime

from kubesage.analyzers.rules.infrastructure.memory_pressure import MemoryPressureRule
from kubesage.models.evidence import EvidenceType
from kubesage.models.finding import FindingKind, Severity
from kubesage.models.incident import Incident
from kubesage.models.kubernetes_snapshot import Event


def test_memory_pressure_detected() -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Running",
        observed_at=datetime.now(),
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
    assert findings[0].rule == "memory_pressure_eviction"
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
    assert findings[0].structured_evidences[0].type == EvidenceType.EVENT
    assert findings[0].structured_evidences[0].description is not None
    assert "memory pressure" in findings[0].structured_evidences[0].description
