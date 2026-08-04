from uuid import uuid4

import pytest

from kubesage.mappers.analysis_mapper import AnalysisMapper
from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import Analysis
from kubesage.models.finding import Finding, ResourceRef, Severity
from kubesage.models.incident import Incident


@pytest.fixture
def analysis() -> Analysis:
    return Analysis(
        incident=Incident(namespace="default", pod="my-pod", phase="Running"),
        duration_ms=1000,
        report=AIReport(summary="Test summary", root_cause="Test root cause"),
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
        ],
    )


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
        ),
        findings=[],
        duration_ms=1000,
    )

    model = AnalysisMapper.to_model(analysis)

    assert model.phase == "Running"
