from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.builders.context.ai_context_builder import AIContextBuilder
from kubesage.builders.context.container_snapshot_builder import (
    ContainerSnapshotBuilder,
)
from kubesage.builders.incident_intelligence_builder import IncidentIntelligenceBuilder
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import AnalysisTrigger
from kubesage.models.container import ContainerSnapshot
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.models.log import LogSnapshot
from kubesage.models.prometheus import PrometheusResourceUsage
from kubesage.services.ai_service import AIService
from kubesage.services.incident_service import IncidentService
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.services.loki_service import LokiService
from kubesage.services.metrics_service import MetricsService
from kubesage.services.prometheus_service import PrometheusService


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
    kubernetes = Mock(spec=KubernetesService)
    prometheus = Mock(spec=PrometheusService)
    metrics = Mock(spec=MetricsService)
    loki = Mock(spec=LokiService)
    ai = Mock(spec=AIService)
    engine = Mock(spec=DiagnosticEngine)
    ai_context_builder = Mock(spec=AIContextBuilder)
    prompt_builder = Mock(spec=PromptBuilder)
    container_snapshot_builder = Mock(
        spec=ContainerSnapshotBuilder,
    )
    incident_intelligence_builder = Mock(
        spec=IncidentIntelligenceBuilder,
    )

    engine.analyze.return_value = findings or []
    if incident is None:
        incident = build_incident()

    kubernetes.collect.return_value = SimpleNamespace(
        namespace=incident.namespace,
        pod=incident.pod,
        pod_uid=incident.pod_uid,
        phase=incident.phase,
        containers=[],
        events=incident.events,
        logs=incident.kubernetes_logs,
        resources=[],
    )

    prometheus.collect.return_value = PrometheusResourceUsage(containers=[])

    metrics.collect.return_value = None
    loki.collect.return_value = None

    container_snapshot_builder.build.return_value = incident.containers

    incident_intelligence_builder.build.return_value = IncidentIntelligence(
        findings=findings or [],
        timeline=[],
        correlations=[],
        root_causes=[],
    )

    service = IncidentService(
        kubernetes=kubernetes,
        prometheus=prometheus,
        metrics=metrics,
        loki=loki,
        ai=ai,
        engine=engine,
        ai_context_builder=ai_context_builder,
        prompt_builder=prompt_builder,
        container_snapshot_builder=container_snapshot_builder,
        incident_intelligence_builder=incident_intelligence_builder,
    )

    return service, {
        "ai": ai,
        "engine": engine,
        "ai_context_builder": ai_context_builder,
        "prompt_builder": prompt_builder,
        "incident_intelligence_builder": incident_intelligence_builder,
    }


def test_analysis_with_findings_calls_ai() -> None:
    finding = Mock(spec=Finding)
    service, mocks = build_service(findings=[finding])

    mocks["ai_context_builder"].build.return_value = Mock()
    mocks["prompt_builder"].build.return_value = "prompt"

    report = AIReport(summary="summary", root_cause="root cause", evidence=[])
    mocks["ai"].analyze.return_value = report

    result = service.analyze(
        namespace="production",
        pod="payment-api",
        trigger=AnalysisTrigger.API,
    )

    assert result.intelligence.findings == [finding]
    assert result.report == report
    assert result.trigger == AnalysisTrigger.API

    mocks["ai"].analyze.assert_called_once_with("prompt")


def test_analysis_without_findings_skips_ai() -> None:
    service, mocks = build_service(findings=[])

    result = service.analyze(
        namespace="production",
        pod="payment-api",
        trigger=AnalysisTrigger.WATCHER,
    )

    assert result.intelligence.findings == []
    assert result.report is None

    mocks["ai"].analyze.assert_not_called()
    mocks["ai_context_builder"].build.assert_not_called()
    mocks["prompt_builder"].build.assert_not_called()


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

    mocks["ai"].analyze.assert_not_called()


def test_analysis_passes_trigger() -> None:
    service, _ = build_service(findings=[])

    result = service.analyze(
        namespace="production",
        pod="payment-api",
        trigger=AnalysisTrigger.CLI,
    )

    assert result.trigger == AnalysisTrigger.CLI
