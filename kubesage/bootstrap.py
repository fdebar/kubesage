from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.builders.context.ai_context_builder import AIContextBuilder
from kubesage.builders.context.container_snapshot_builder import (
    ContainerSnapshotBuilder,
)
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.services.ai_service import AIService
from kubesage.services.incident_service import IncidentService
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.services.loki_service import LokiService
from kubesage.services.metrics_service import MetricsService
from kubesage.services.prometheus_service import PrometheusService


def create_incident_service() -> IncidentService:
    return IncidentService(
        kubernetes=KubernetesService(),
        prometheus=PrometheusService(),
        loki=LokiService(),
        metrics=MetricsService(),
        ai=AIService(),
        engine=DiagnosticEngine(),
        ai_context_builder=AIContextBuilder(),
        prompt_builder=PromptBuilder(),
        container_snapshot_builder=ContainerSnapshotBuilder(),
    )
