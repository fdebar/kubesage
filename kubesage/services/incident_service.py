import time

import structlog
from opentelemetry import trace

from kubesage.analyzers.engine import DiagnosticEngine
from kubesage.builders.context.container_snapshot_builder import (
    ContainerSnapshotBuilder,
)
from kubesage.builders.context.incident_builder import IncidentBuilder
from kubesage.builders.incident_intelligence_builder import (
    IncidentIntelligenceBuilder,
)
from kubesage.models.ai_report import AIReport
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.services.ai_report_generator import AIReportGenerator
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.services.loki_service import LokiService
from kubesage.services.metrics_service import MetricsService
from kubesage.services.prometheus_service import PrometheusService

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger()


class IncidentService:
    def __init__(
        self,
        ai_report_generator: AIReportGenerator,
        kubernetes: KubernetesService,
        prometheus: PrometheusService | None,
        metrics: MetricsService,
        loki: LokiService | None,
        engine: DiagnosticEngine,
        container_snapshot_builder: ContainerSnapshotBuilder,
        incident_intelligence_builder: IncidentIntelligenceBuilder,
    ) -> None:
        self.kubernetes = kubernetes
        self.prometheus = prometheus
        self.metrics = metrics
        self.loki = loki
        self.engine = engine
        self.container_snapshot_builder = container_snapshot_builder
        self.incident_intelligence_builder = incident_intelligence_builder
        self.ai_report_generator = ai_report_generator

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

            if incident.pod_uid:
                span.set_attribute("k8s.pod.uid", incident.pod_uid)

            loki_logs_count = (
                len(incident.loki_logs.entries) if incident.loki_logs else 0
            )
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
                    ),
                    incident=incident,
                    intelligence=IncidentIntelligence(),
                    duration_ms=int((time.perf_counter() - start) * 1000),
                    trigger=trigger,
                )

        with tracer.start_as_current_span("analysis.rules.engine.analyze") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)
            span.set_attribute("analysis.trigger", trigger.value)

            findings = self.engine.analyze(incident)

            span.set_attribute("analysis.findings.count", len(findings))

        with tracer.start_as_current_span(
            "analysis.incident_intelligence.build"
        ) as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)
            span.set_attribute("analysis.trigger", trigger.value)
            span.set_attribute("analysis.findings.count", len(findings))

            intelligence = self.incident_intelligence_builder.build(
                incident,
                findings,
            )

            span.set_attribute(
                "incident_intelligence.timeline.count",
                len(intelligence.timeline),
            )
            span.set_attribute(
                "incident_intelligence.correlations.count",
                len(intelligence.correlations),
            )
            span.set_attribute(
                "incident_intelligence.root_causes.count",
                len(intelligence.root_causes),
            )

        if not findings:
            logger.info("analysis.skipped", namespace=namespace, pod=pod)

            return Analysis(
                incident=incident,
                report=None,
                duration_ms=int((time.perf_counter() - start) * 1000),
                trigger=trigger,
                intelligence=intelligence,
            )

        with tracer.start_as_current_span("analysis.ai_report.generate") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)
            span.set_attribute("analysis.trigger", trigger.value)

            report = self.ai_report_generator.generate(incident, intelligence)

        logger.info("analysis.completed", namespace=namespace, pod=pod, trigger=trigger)

        return Analysis(
            incident=incident,
            report=report,
            intelligence=intelligence,
            duration_ms=int((time.perf_counter() - start) * 1000),
            trigger=trigger,
        )
