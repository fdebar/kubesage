from datetime import datetime

from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.incident import Incident


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
        findings=[],
        report=report,
        duration_ms=100,
        trigger=AnalysisTrigger.API,
    )

    assert analysis.report == report
    assert analysis.duration_ms == 100
