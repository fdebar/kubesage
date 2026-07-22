from kubesage.builders.context_builder import ContextBuilder
from kubesage.builders.prompt_builder import PromptBuilder
from kubesage.services.prometheus_service import PrometheusService
from kubesage.services.metrics_service import MetricsService
from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.services.ai_service import AIService
from kubesage.observability.factory import get_logger


class IncidentService:
    def __init__(self) -> None:
        self.kubernetes = KubernetesService()
        self.engine = DiagnosticEngine()
        self.ai = AIService()
        self.metrics = MetricsService()
        self.prometheus = PrometheusService()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()
        self.logger = get_logger(__name__)

    def analyze(self, namespace: str, pod: str) -> dict:
        self.logger.info("CLI analysis started")

        incident = self.kubernetes.collect(namespace, pod)
        incident.metrics = self.metrics.collect(namespace, pod)
        incident.prometheus = self.prometheus.collect(namespace, pod)

        findings = self.engine.analyze(incident)
        ctxbuilder = self.context_builder.build(incident, findings)
        prompt = self.prompt_builder.build(ctxbuilder)
        report = self.ai.analyze(prompt)

        return report
