from sqlalchemy.orm import Session

from kubesage.ai.factory import create_ai_provider
from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.builders.context.ai_context_builder import AIContextBuilder
from kubesage.builders.context.container_snapshot_builder import (
    ContainerSnapshotBuilder,
)
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.database.health import (
    check_database_availability,
)
from kubesage.observability import setup_logging
from kubesage.repositories.analysis_repository import AnalysisRepository
from kubesage.services.ai_service import AIService
from kubesage.services.analysis_service import AnalysisService
from kubesage.services.incident_service import IncidentService
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.services.loki_service import LokiService
from kubesage.services.metrics_service import MetricsService
from kubesage.services.prometheus_service import PrometheusService
from kubesage.utils.config import settings


def create_incident_service() -> IncidentService:
    return IncidentService(
        kubernetes=KubernetesService(),
        prometheus=PrometheusService(),
        loki=LokiService(),
        metrics=MetricsService(),
        ai=AIService(create_ai_provider(settings=settings)),
        engine=DiagnosticEngine(),
        ai_context_builder=AIContextBuilder(),
        prompt_builder=PromptBuilder(),
        container_snapshot_builder=ContainerSnapshotBuilder(),
    )


def create_analysis_service(db: Session) -> AnalysisService:
    return AnalysisService(
        incident_service=create_incident_service(),
        repository=AnalysisRepository(db),
    )


def check_application_requirements() -> None:
    check_database_availability()
    setup_logging()
