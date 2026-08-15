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
        prometheus: PrometheusService | None,
        metrics: MetricsService,
        loki: LokiService | None,
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
        logger.info("analysis.started", namespace=namespace, pod=pod, trigger=trigger)

        start = time.perf_counter()

        with tracer.start_as_current_span("analysis.incident.build") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)
            span.set_attribute("analysis.trigger", trigger.value)

            builder = IncidentBuilder(
                kubernetes_provider=self.kubernetes,
                prometheus_provider=self.prometheus,
                log_provider=self.loki,
                metrics_provider=self.metrics,
                container_snapshot_builder=self.container_snapshot_builder,
            )

            incident = builder.collect(namespace, pod)
            span.set_attribute("k8s.containers.count", len(incident.containers))
            span.set_attribute("k8s.events.count", len(incident.events))

            loki_logs_count = len(incident.loki_logs.lines) if incident.loki_logs else 0
            span.set_attribute("loki.logs.count", loki_logs_count)

            if not incident.containers and not incident.events:
                logger.error(
                    "analysis.incident.build.no_kubernetes_data",
                    namespace=namespace,
                    pod=pod,
                )

                return Analysis(
                    report=AIReport(
                        summary=(
                            "AI analysis could not be completed due to "
                            "unavailable Kubernetes data."
                        ),
                        root_cause=(
                            "Kubernetes data collection failed. This could "
                            "be due to authentication issues, network "
                            "problems, or the pod not existing."
                        ),
                        evidence=[],
                    ),
                    incident=incident,
                    findings=[],
                    duration_ms=int((time.perf_counter() - start) * 1000),
                    trigger=trigger,
                )

        with tracer.start_as_current_span("analysis.rules.engine.analyze") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)
            span.set_attribute("analysis.trigger", trigger.value)

            findings = self.engine.analyze(incident)

            span.set_attribute("analysis.findings.count", len(findings))

        if not findings:
            logger.info("analysis.skipped", namespace=namespace, pod=pod)

            return Analysis(
                incident=incident,
                findings=findings,
                report=None,
                duration_ms=int((time.perf_counter() - start) * 1000),
                trigger=trigger,
            )

        with tracer.start_as_current_span("analysis.ai_context.build") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)
            span.set_attribute("analysis.trigger", trigger.value)

            context = self.ai_context_builder.build(incident, findings)

        with tracer.start_as_current_span("analysis.ai_prompt.build") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)
            span.set_attribute("analysis.trigger", trigger.value)

            prompt = self.prompt_builder.build(context)

        with tracer.start_as_current_span("analysis.ai.analyze") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)
            span.set_attribute("analysis.trigger", trigger.value)

            report = self.ai.analyze(prompt)

        logger.info("analysis.completed", namespace=namespace, pod=pod, trigger=trigger)

        return Analysis(
            incident=incident,
            findings=findings,
            report=report,
            duration_ms=int((time.perf_counter() - start) * 1000),
            trigger=trigger,
        )
