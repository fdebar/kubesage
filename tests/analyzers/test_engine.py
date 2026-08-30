from datetime import datetime

from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.models.incident import Incident
from kubesage.services.findings_correlator import FindingsCorrelator


def _test_engine_rules_not_empty() -> None:
    engine = DiagnosticEngine()

    assert len(engine.rules) > 0


def _test_engine_correlator() -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Running",
        observed_at=datetime.now(),
    )
    engine = DiagnosticEngine(correlator=FindingsCorrelator())
    findings = engine.analyze(incident=incident)

    assert isinstance(engine.correlator, FindingsCorrelator)
    assert findings != []


def _test_engine_correlator_none() -> None:
    incident = Incident(
        namespace="test",
        pod="test",
        phase="Running",
        observed_at=datetime.now(),
    )
    engine = DiagnosticEngine(correlator=None)
    findings = engine.analyze(incident=incident)

    assert isinstance(engine.correlator, FindingsCorrelator)
    assert findings != []
