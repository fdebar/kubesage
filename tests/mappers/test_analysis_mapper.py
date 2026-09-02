from datetime import datetime
from uuid import uuid4

import pytest

from kubesage.mappers.analysis_mapper import AnalysisMapper
from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.finding import Finding, ResourceRef, Severity
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import (
    Correlation,
    CorrelationType,
    IncidentIntelligence,
    RootCauseCandidate,
)


@pytest.fixture
def analysis() -> Analysis:
    return Analysis(
        incident=Incident(
            namespace="default",
            pod="my-pod",
            phase="Running",
            observed_at=datetime.now(),
        ),
        duration_ms=1000,
        report=AIReport(summary="Test summary", root_cause="Test root cause"),
        intelligence=IncidentIntelligence(
            findings=[
                Finding(
                    rule="crash_loop",
                    severity=Severity.HIGH,
                    title="Container restarting",
                    description="Container restarted 10 times",
                    resource=ResourceRef(
                        api_version="v1",
                        kind="Pod",
                        namespace="default",
                        name="my-pod",
                    ),
                )
            ]
        ),
        trigger=AnalysisTrigger.API,
    )


def test_analysis_mapper_creates_complete_model(analysis: Analysis) -> None:
    model = AnalysisMapper.to_model(analysis)

    assert model.id == str(analysis.id)
    assert model.namespace == "default"
    assert model.pod == "my-pod"
    assert model.duration_ms == 1000

    assert model.summary == "Test summary"
    assert model.phase == "Running"

    assert model.findings_count == 1
    assert len(model.findings) == 1
    assert model.findings[0].rule == "crash_loop"

    assert model.report is not None
    assert model.report.summary == "Test summary"

    assert model.incident_snapshot is not None
    assert model.incident_snapshot.data["namespace"] == "default"


def test_to_model_without_report() -> None:
    analysis = Analysis(
        incident=Incident(
            namespace="default",
            pod="test-pod",
            phase="Failed",
            observed_at=datetime.now(),
        ),
        duration_ms=500,
        trigger=AnalysisTrigger.API,
    )
    model = AnalysisMapper.to_model(analysis)

    assert model.report is None
    assert model.summary is None


def test_to_model_calculates_findings_count() -> None:
    analysis = Analysis(
        incident=Incident(
            namespace="default",
            pod="pod",
            phase="Running",
            observed_at=datetime.now(),
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
        duration_ms=500,
        trigger=AnalysisTrigger.API,
    )
    model = AnalysisMapper.to_model(analysis)

    assert model.findings_count == 2


def test_to_model_maps_highest_severity() -> None:
    analysis = Analysis(
        incident=Incident(
            namespace="default",
            pod="pod",
            phase="Running",
            observed_at=datetime.now(),
        ),
        intelligence=IncidentIntelligence(
            findings=[
                Finding(
                    rule="critical_rule",
                    severity=Severity.CRITICAL,
                    title="Critical finding",
                    description="Critical issue detected",
                )
            ]
        ),
        duration_ms=500,
        trigger=AnalysisTrigger.API,
    )
    model = AnalysisMapper.to_model(analysis)

    assert model.highest_severity == Severity.CRITICAL.value


def test_to_domain_restores_analysis(analysis: Analysis) -> None:
    model = AnalysisMapper.to_model(analysis)
    domain = AnalysisMapper.to_domain(model)

    assert domain.id == analysis.id
    assert domain.incident.namespace == "default"
    assert domain.incident.pod == "my-pod"
    assert domain.incident.phase == "Running"

    assert len(domain.intelligence.findings) == 1
    assert domain.intelligence.findings[0].rule == "crash_loop"

    assert domain.report is not None
    assert domain.report.summary == "Test summary"


def test_analysis_mapper_creates_model(analysis: Analysis) -> None:
    model = AnalysisMapper.to_model(analysis)

    assert model.namespace == "default"
    assert len(model.findings) == 1
    assert model.findings[0].rule == "crash_loop"


def test_to_model_keeps_incident_phase() -> None:
    analysis = Analysis(
        id=uuid4(),
        incident=Incident(
            namespace="default",
            pod="test-pod",
            phase="Running",
            observed_at=datetime.now(),
        ),
        duration_ms=1000,
        trigger=AnalysisTrigger.API,
    )
    model = AnalysisMapper.to_model(analysis)

    assert model.phase == "Running"


def test_analysis_intelligence_round_trip() -> None:
    intelligence = IncidentIntelligence(
        timeline=[],
        correlations=[
            Correlation(
                source_finding="memory_exhaustion",
                target_finding="oom_killed",
                type=CorrelationType.CAUSED_BY,
                confidence=1.0,
            )
        ],
        root_causes=[
            RootCauseCandidate(
                finding="memory_exhaustion",
                title="Memory exhaustion",
                description="Memory exhaustion detected.",
                confidence=1.0,
                supporting_findings=["oom_killed"],
            )
        ],
    )

    incident = Incident(
        namespace="default",
        pod="test-pod",
        phase="Running",
        observed_at=datetime.now(),
    )
    analysis = Analysis(
        trigger=AnalysisTrigger.API,
        incident=incident,
        intelligence=intelligence,
        report=None,
        duration_ms=100,
    )

    model = AnalysisMapper.to_model(analysis)
    restored = AnalysisMapper.to_domain(model)

    assert restored.intelligence.correlations == intelligence.correlations
    assert restored.intelligence.root_causes == intelligence.root_causes
