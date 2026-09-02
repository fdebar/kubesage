from sqlalchemy.orm import Session

from kubesage.ai.factory import create_ai_provider
from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.builders.context.ai_context_builder import AIContextBuilder
from kubesage.builders.context.incident_builder import IncidentBuilder
from kubesage.builders.incident_intelligence_builder import IncidentIntelligenceBuilder
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.database.health import (
    check_database_availability,
)
from kubesage.observability import setup_logging
from kubesage.repositories.analysis_repository import AnalysisRepository
from kubesage.services.ai_report_generator import AIReportGenerator
from kubesage.services.ai_service import AIService
from kubesage.services.analysis_service import AnalysisService
from kubesage.services.incident_service import IncidentService
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.services.loki_service import LokiService
from kubesage.services.metrics_service import MetricsService
from kubesage.services.prometheus_service import PrometheusService
from kubesage.utils.config import settings


def create_incident_service() -> IncidentService:
    prometheus = PrometheusService() if settings.prometheus_url else None
    loki = LokiService() if settings.loki_url else None

    incident_builder = IncidentBuilder(
        kubernetes_provider=KubernetesService(),
        prometheus_provider=prometheus,
        metrics_provider=MetricsService(),
        log_provider=loki,
    )

    ai_report_generator = AIReportGenerator(
        ai=AIService(create_ai_provider(settings=settings)),
        context_builder=AIContextBuilder(),
        prompt_builder=PromptBuilder(),
    )

    return IncidentService(
        ai_report_generator=ai_report_generator,
        incident_builder=incident_builder,
        engine=DiagnosticEngine(),
        incident_intelligence_builder=IncidentIntelligenceBuilder(),
    )


def create_analysis_service(db: Session) -> AnalysisService:
    return AnalysisService(
        incident_service=create_incident_service(),
        repository=AnalysisRepository(db),
    )


def check_application_requirements() -> None:
    check_database_availability()
    setup_logging()
