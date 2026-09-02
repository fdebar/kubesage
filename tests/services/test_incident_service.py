from datetime import datetime
from unittest.mock import Mock

from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.builders.context.incident_builder import IncidentBuilder
from kubesage.builders.incident_intelligence_builder import IncidentIntelligenceBuilder
from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import AnalysisTrigger
from kubesage.models.container import ContainerSnapshot
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.models.log import LogSnapshot
from kubesage.services.ai_report_generator import AIReportGenerator
from kubesage.services.incident_service import IncidentService


def build_container() -> ContainerSnapshot:
    return ContainerSnapshot(
        name="payment-api",
        image="payment-api:latest",
        ready=True,
        restart_count=0,
    )


def build_incident(
    *,
    containers: list[ContainerSnapshot] | None = None,
    events: list | None = None,
) -> Incident:
    return Incident(
        namespace="production",
        pod="payment-api",
        pod_uid="123e4567-e89b-12d3-a456-426614174000",
        phase="Running",
        observed_at=datetime.now(),
        containers=containers if containers is not None else [build_container()],
        events=events if events is not None else [],
        kubernetes_logs=LogSnapshot(source="kubernetes"),
        loki_logs=None,
        prometheus=None,
        metrics=None,
    )


def build_service(
    *,
    findings: list[Finding] | None = None,
    incident: Incident | None = None,
) -> tuple[IncidentService, dict[str, Mock]]:
    engine = Mock(spec=DiagnosticEngine)
    incident_builder = Mock(spec=IncidentBuilder)
    incident_intelligence_builder = Mock(
        spec=IncidentIntelligenceBuilder,
    )
    ai_report_generator = Mock(spec=AIReportGenerator)

    engine.analyze.return_value = findings or []

    if incident is None:
        incident = build_incident()

    incident_builder.collect.return_value = incident

    incident_intelligence_builder.build.return_value = IncidentIntelligence(
        findings=findings or [],
        timeline=[],
        correlations=[],
        root_causes=[],
    )

    service = IncidentService(
        ai_report_generator=ai_report_generator,
        engine=engine,
        incident_builder=incident_builder,
        incident_intelligence_builder=incident_intelligence_builder,
    )

    return service, {
        "ai_report_generator": ai_report_generator,
        "engine": engine,
        "incident_builder": incident_builder,
        "incident_intelligence_builder": incident_intelligence_builder,
    }


def test_analysis_with_findings_calls_ai() -> None:
    finding = Mock(spec=Finding)
    service, mocks = build_service(findings=[finding])

    report = AIReport(summary="summary", root_cause="root cause", evidence=[])
    mocks["ai_report_generator"].generate.return_value = report

    result = service.analyze(
        namespace="production",
        pod="payment-api",
        trigger=AnalysisTrigger.API,
    )

    assert result.intelligence.findings == [finding]
    assert result.report == report
    assert result.trigger == AnalysisTrigger.API

    mocks["ai_report_generator"].generate.assert_called_once()


def test_analysis_without_findings_skips_ai() -> None:
    service, mocks = build_service(findings=[])

    result = service.analyze(
        namespace="production",
        pod="payment-api",
        trigger=AnalysisTrigger.WATCHER,
    )

    assert result.intelligence.findings == []
    assert result.report is None

    mocks["ai_report_generator"].generate.assert_not_called()


def test_analysis_when_kubernetes_data_is_unavailable_returns_error_report() -> None:
    incident = build_incident(containers=[], events=[])
    service, mocks = build_service(incident=incident)
    result = service.analyze(
        namespace="production",
        pod="payment-api",
        trigger=AnalysisTrigger.WATCHER,
    )

    assert result.report is not None
    assert (
        result.report.summary
        == "AI analysis could not be completed due to unavailable Kubernetes data."
    )

    mocks["ai_report_generator"].generate.assert_not_called()


def test_analysis_passes_trigger() -> None:
    service, _ = build_service(findings=[])

    result = service.analyze(
        namespace="production",
        pod="payment-api",
        trigger=AnalysisTrigger.CLI,
    )

    assert result.trigger == AnalysisTrigger.CLI
