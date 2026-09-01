from datetime import UTC, datetime
from uuid import uuid4

from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence


def build_analysis(report: AIReport | None = None) -> Analysis:
    return Analysis(
        id=uuid4(),
        incident=Incident(
            namespace="test-namespace",
            pod="test-pod",
            phase="Running",
            pod_uid="test-pod-uid",
            observed_at=datetime.now(UTC),
        ),
        findings=[],
        intelligence=IncidentIntelligence(
            correlations=[],
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
