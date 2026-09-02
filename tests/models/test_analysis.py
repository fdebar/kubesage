from datetime import datetime

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
