from services.prometheus_service import PrometheusService
from services.metrics_service import MetricsService
from analyzers.engine import DiagnosticEngine
from services.kubernetes_service import KubernetesService
from services.ai_service import AIService
from utils.prompt_builder import build_prompt


class IncidentService:

    def __init__(self):

        self.kubernetes = KubernetesService()
        self.engine = DiagnosticEngine()
        self.ai = AIService()
        self.metrics = MetricsService()
        self.prometheus = PrometheusService()

    def analyze(
        self,
        namespace,
        pod,
    ):

        incident = self.kubernetes.collect(namespace, pod)
        incident.metrics = self.metrics.collect(namespace, pod)
        incident.prometheus = self.prometheus.collect(namespace, pod)

        with open("prompts/sre_analysis.txt") as f:
            template = f.read()

        findings = self.engine.analyze(incident)
        prompt = build_prompt(incident, findings, template)
        report = self.ai.analyze(prompt)

        return report
