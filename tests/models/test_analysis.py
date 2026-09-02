from datetime import UTC, datetime
from uuid import uuid4

from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.finding import Finding, Severity
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence


def test_analysis_contains_report() -> None:
    report = AIReport(
        summary="Test summary",
        root_cause="Test root cause",
        evidence=[],
    )

    analysis = Analysis(
        incident=Incident(
            namespace="default",
            pod="my-pod",
            phase="Running",
            observed_at=datetime.now(),
            containers=[],
            events=[],
            loki_logs=None,
            prometheus=None,
            metrics=None,
        ),
        report=report,
        duration_ms=100,
        trigger=AnalysisTrigger.API,
    )

    assert analysis.report == report
    assert analysis.duration_ms == 100


def test_analysis_contains_findings() -> None:
    analysis = Analysis(
        incident=Incident(
            namespace="default",
            pod="my-pod",
            phase="Running",
            observed_at=datetime.now(),
            containers=[],
            events=[],
            loki_logs=None,
            prometheus=None,
            metrics=None,
        ),
        intelligence=IncidentIntelligence(
            findings=[
                Finding(
                    rule="rule1",
                    severity=Severity.HIGH,
                    title="Finding 1",
                    description="desc",
                ),
                Finding(
                    rule="rule2",
                    severity=Severity.LOW,
                    title="Finding 2",
                    description="desc",
                ),
            ]
        ),
        duration_ms=100,
        trigger=AnalysisTrigger.API,
    )

    assert len(analysis.intelligence.findings) == 2


def build_analysis(trace_id: str | None = None) -> Analysis:
    return Analysis(
        id=uuid4(),
        incident=Incident(
            namespace="default",
            pod="test-pod",
            pod_uid="test-pod-uid",
            phase="Running",
            containers=[],
            observed_at=datetime.now(UTC),
        ),
        intelligence=IncidentIntelligence(
            findings=[],
            timeline=[],
            correlations=[],
            root_causes=[],
            recommendations=[],
        ),
        report=None,
        trigger=AnalysisTrigger.API,
        created_at=datetime.now(UTC),
        duration_ms=100,
        trace_id=trace_id,
    )


def test_analysis_trace_id_defaults_to_none() -> None:
    analysis = build_analysis()

    assert analysis.trace_id is None


def test_analysis_accepts_trace_id() -> None:
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    analysis = build_analysis(trace_id=trace_id)

    assert analysis.trace_id == trace_id
