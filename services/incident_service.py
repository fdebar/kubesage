from builders.context_builder import ContextBuilder
from builders.prompt_builder import PromptBuilder
from services.prometheus_service import PrometheusService
from services.metrics_service import MetricsService
from analyzers.engine import DiagnosticEngine
from services.kubernetes_service import KubernetesService
from services.ai_service import AIService


class IncidentService:

    def __init__(self):

        self.kubernetes = KubernetesService()
        self.engine = DiagnosticEngine()
        self.ai = AIService()
        self.metrics = MetricsService()
        self.prometheus = PrometheusService()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()

    def analyze(
        self,
        namespace,
        pod,
    ):

        incident = self.kubernetes.collect(namespace, pod)
        incident.metrics = self.metrics.collect(namespace, pod)
        incident.prometheus = self.prometheus.collect(namespace, pod)

        findings = self.engine.analyze(incident)
        context = self.context_builder.build(incident, findings)
        prompt = self.prompt_builder.build(context)
        report = self.ai.analyze(prompt)

        return report
