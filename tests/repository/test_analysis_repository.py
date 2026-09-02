from datetime import UTC, datetime
from unittest.mock import MagicMock

from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.repositories.analysis_repository import AnalysisRepository


def build_analysis(report: AIReport | None = None) -> Analysis:
    return Analysis(
        incident=Incident(
            namespace="test-namespace",
            pod="test-pod",
            phase="Running",
            pod_uid="test-pod-uid",
            observed_at=datetime.now(UTC),
        ),
        intelligence=IncidentIntelligence(
            correlations=[],
            findings=[],
            root_causes=[],
            recommendations=[],
        ),
        report=(
            report
            if report is not None
            else AIReport(
                summary="Test summary",
                root_cause="Test root cause",
                confidence=0.5,
                impact="Test impact",
                findings=[],
                evidence=[],
                recommendations=[],
                additional_investigations=[],
            )
        ),
        trigger=AnalysisTrigger.API,
        created_at=datetime.now(UTC),
        duration_ms=100,
    )


def test_save_and_get_preserves_trace_id() -> None:
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"

    analysis = build_analysis()
    analysis.trace_id = trace_id

    session = MagicMock()
    repository = AnalysisRepository(session)

    repository.save(analysis)

    saved_model = session.add.call_args.args[0]
    session.execute.return_value.scalar_one_or_none.return_value = saved_model

    restored = repository.get(analysis.id)

    assert restored is not None
    assert restored.trace_id == trace_id
