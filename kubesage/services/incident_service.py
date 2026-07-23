from kubesage.builders.context_builder import ContextBuilder
from kubesage.builders.prompt_builder import PromptBuilder
from kubesage.services.prometheus_service import PrometheusService
from kubesage.services.metrics_service import MetricsService
from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.services.ai_service import AIService
from opentelemetry import trace
import structlog

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger()


class IncidentService:
    def __init__(self) -> None:
        self.kubernetes = KubernetesService()
        self.engine = DiagnosticEngine()
        self.ai = AIService()
        self.metrics = MetricsService()
        self.prometheus = PrometheusService()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()

    def analyze(self, namespace: str, pod: str) -> dict:
        logger.info(
            "analysis_started",
            namespace=namespace,
            pod=pod,
        )

        with tracer.start_as_current_span("collect_kubernetes_data") as span:
            span.set_attribute("namespace", namespace)
            span.set_attribute("pod", pod)
            incident = self.kubernetes.collect(namespace, pod)
        trace.get_current_span()

        with tracer.start_as_current_span("collect_metrics") as span:
            span.set_attribute("namespace", namespace)
            span.set_attribute("pod", pod)
            incident.metrics = self.metrics.collect(namespace, pod)
        trace.get_current_span()

        with tracer.start_as_current_span("query_prometheus") as span:
            span.set_attribute("namespace", namespace)
            span.set_attribute("pod", pod)
            incident.prometheus = self.prometheus.collect(namespace, pod)
        trace.get_current_span()

        with tracer.start_as_current_span("run_rules_engine") as span:
            span.set_attribute("namespace", namespace)
            span.set_attribute("pod", pod)
            findings = self.engine.analyze(incident)
        trace.get_current_span()

        with tracer.start_as_current_span("build_ai_context") as span:
            span.set_attribute("namespace", namespace)
            span.set_attribute("pod", pod)
            ctxbuilder = self.context_builder.build(incident, findings)
        trace.get_current_span()

        with tracer.start_as_current_span("build_ai_prompt") as span:
            span.set_attribute("namespace", namespace)
            span.set_attribute("pod", pod)
            prompt = self.prompt_builder.build(ctxbuilder)
        trace.get_current_span()

        with tracer.start_as_current_span("call_openai") as span:
            span.set_attribute("namespace", namespace)
            span.set_attribute("pod", pod)
            report = self.ai.analyze(prompt)
            span.set_attribute("llm.response_length", len(report.get("summary", "")))
        trace.get_current_span()

        return report
