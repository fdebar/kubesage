import time

import structlog
from opentelemetry import trace

from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.builders.context.ai_context_builder import AIContextBuilder
from kubesage.builders.context.container_snapshot_builder import (
    ContainerSnapshotBuilder,
)
from kubesage.builders.context.incident_builder import IncidentBuilder
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.services.ai_service import AIService
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.services.loki_service import LokiService
from kubesage.services.metrics_service import MetricsService
from kubesage.services.prometheus_service import PrometheusService

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger()


class IncidentService:
    def __init__(
        self,
        kubernetes: KubernetesService,
        prometheus: PrometheusService,
        metrics: MetricsService,
        loki: LokiService,
        ai: AIService,
        engine: DiagnosticEngine,
        ai_context_builder: AIContextBuilder,
        prompt_builder: PromptBuilder,
        container_snapshot_builder: ContainerSnapshotBuilder,
    ) -> None:
        self.kubernetes = kubernetes
        self.prometheus = prometheus
        self.metrics = metrics
        self.loki = loki
        self.ai = ai
        self.engine = engine
        self.ai_context_builder = ai_context_builder
        self.prompt_builder = prompt_builder
        self.container_snapshot_builder = container_snapshot_builder

    def analyze(self, namespace: str, pod: str, trigger: AnalysisTrigger) -> Analysis:
        logger.info("analysis_started", namespace=namespace, pod=pod, trigger=trigger)

        start = time.perf_counter()

        with tracer.start_as_current_span("incident.build") as span:
            span.set_attribute("incident.namespace", namespace)
            span.set_attribute("incident.pod", pod)
            self.builder = IncidentBuilder(
                kubernetes_provider=self.kubernetes,
                prometheus_provider=self.prometheus,
                log_provider=self.loki,
                metrics_provider=self.metrics,
                container_snapshot_builder=self.container_snapshot_builder,
            )

            incident = self.builder.collect(namespace, pod)
            if incident.containers == [] and incident.events == []:
                logger.error("kubernetes_no_data")
                return Analysis(
                    report=AIReport(
                        summary="AI analysis could not be completed due to unavailable Kubernetes data.",  # noqa
                        root_cause="Kubernetes data collection failed. This could be due to authentication issues, network problems, or the pod not existing.",  # noqa
                        evidence=[],
                    ),
                    incident=incident,
                    findings=[],
                    duration_ms=int((time.perf_counter() - start) * 1000),
                    trigger=trigger,
                )

        with tracer.start_as_current_span("rules.engine.analyze") as span:
            span.set_attribute("rules.namespace", namespace)
            span.set_attribute("rules.pod", pod)
            findings = self.engine.analyze(incident)

            span.set_attribute("rules.count", len(findings))

        with tracer.start_as_current_span("ai_context.build") as span:
            span.set_attribute("ai_context.namespace", namespace)
            span.set_attribute("ai_context.pod", pod)
            ctxbuilder = self.ai_context_builder.build(incident, findings)

        with tracer.start_as_current_span("ai_prompt.build") as span:
            span.set_attribute("ai_prompt.namespace", namespace)
            span.set_attribute("ai_prompt.pod", pod)
            prompt = self.prompt_builder.build(ctxbuilder)

        with tracer.start_as_current_span("llm.analyze") as span:
            span.set_attribute("llm.namespace", namespace)
            span.set_attribute("llm.pod", pod)
            report = self.ai.analyze(prompt)

        logger.info("analysis_completed", namespace=namespace, pod=pod, trigger=trigger)

        analysis = Analysis(
            incident=incident,
            findings=findings,
            report=report,
            duration_ms=int((time.perf_counter() - start) * 1000),
            trigger=trigger,
        )

        return analysis
