import structlog
from opentelemetry import trace

from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.builders.context.ai_context_builder import AIContextBuilder
from kubesage.builders.context.incident_builder import IncidentBuilder
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.incident import Incident
from kubesage.services.ai_service import AIService
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.services.loki_service import LokiService
from kubesage.services.metrics_service import MetricsService
from kubesage.services.prometheus_service import PrometheusService

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger()


class IncidentService:
    def __init__(self) -> None:
        self.incident: Incident | None = None
        self.kubernetes = KubernetesService()
        self.engine = DiagnosticEngine()
        self.ai = AIService()
        self.metrics = MetricsService()
        self.prometheus = PrometheusService()
        self.loki = LokiService()
        self.ai_context_builder = AIContextBuilder()
        self.prompt_builder = PromptBuilder()

    def analyze(self, namespace: str, pod: str) -> dict:
        logger.info("analysis_started", namespace=namespace, pod=pod)

        with tracer.start_as_current_span("build_incident") as span:
            span.set_attribute("incident.namespace", namespace)
            span.set_attribute("incident.pod", pod)
            self.builder = IncidentBuilder(
                kubernetes_provider=self.kubernetes,
                prometheus_provider=self.prometheus,
                log_provider=self.loki,
                metrics_provider=self.metrics,
            )

            incident = self.builder.collect(namespace, pod)

        with tracer.start_as_current_span("run_rules_engine") as span:
            span.set_attribute("rules.namespace", namespace)
            span.set_attribute("rules.pod", pod)
            findings = self.engine.analyze(incident)

            span.set_attribute("rules.count", len(findings))

        with tracer.start_as_current_span("build_ai_context") as span:
            span.set_attribute("ai_context.namespace", namespace)
            span.set_attribute("ai_context.pod", pod)
            ctxbuilder = self.ai_context_builder.build(incident, findings)

        with tracer.start_as_current_span("build_ai_prompt") as span:
            span.set_attribute("ai_prompt.namespace", namespace)
            span.set_attribute("ai_prompt.pod", pod)
            prompt = self.prompt_builder.build(ctxbuilder)
            logger.debug(prompt)

        with tracer.start_as_current_span("call_llm") as span:
            span.set_attribute("llm.namespace", namespace)
            span.set_attribute("llm.pod", pod)
            report = self.ai.analyze(prompt)

            span.set_attribute("llm.response_length", len(report.get("summary", "")))

        logger.info("analysis_completed", namespace=namespace, pod=pod)

        return report
