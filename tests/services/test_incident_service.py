from datetime import datetime
from unittest.mock import MagicMock, patch

from kubesage.models.incident import Incident
from kubesage.models.log import LogSnapshot
from kubesage.services.incident_service import IncidentService


@patch("kubesage.services.incident_service.KubernetesService")
@patch("kubesage.services.incident_service.MetricsService")
@patch("kubesage.services.incident_service.PrometheusService")
@patch("kubesage.services.incident_service.DiagnosticEngine")
@patch("kubesage.services.incident_service.ContextBuilder")
@patch("kubesage.services.incident_service.PromptBuilder")
@patch("kubesage.services.incident_service.AIService")
@patch("kubesage.services.incident_service.IncidentBuilder")
def test_analyze_flow(
    incident_builder_cls: MagicMock,
    ai_cls: MagicMock,
    prompt_builder_cls: MagicMock,
    context_builder_cls: MagicMock,
    engine_cls: MagicMock,
    prometheus_cls: MagicMock,
    metrics_cls: MagicMock,
    kubernetes_cls: MagicMock,
) -> None:
    # Kubernetes
    kubernetes = MagicMock()
    kubernetes_snapshot = MagicMock()
    kubernetes.collect.return_value = kubernetes_snapshot
    kubernetes_cls.return_value = kubernetes

    # Metrics
    metrics = MagicMock()
    metrics_snapshot = MagicMock()
    metrics.collect.return_value = metrics_snapshot
    metrics_cls.return_value = metrics

    # Prometheus
    prometheus = MagicMock()
    prometheus_snapshot = MagicMock()
    prometheus.collect.return_value = prometheus_snapshot
    prometheus_cls.return_value = prometheus

    # IncidentBuilder
    incident = Incident(
        namespace="default",
        pod="my-pod",
        phase="Pending",
        containers=[],
        events=[],
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            collected_at=datetime.fromisoformat("2022-01-01T00:00:00Z"),
            lines=[],
        ),
        loki_logs=None,
        prometheus=None,
        metrics=None,
    )

    incident_builder = MagicMock()
    incident_builder.build.return_value = incident
    incident_builder_cls.return_value = incident_builder

    # Diagnostic engine
    findings = ["finding1", "finding2"]
    engine = MagicMock()
    engine.analyze.return_value = findings
    engine_cls.return_value = engine

    # Context builder
    context = MagicMock()
    context_builder = MagicMock()
    context_builder.build.return_value = context
    context_builder_cls.return_value = context_builder

    # Prompt builder
    prompt_builder = MagicMock()
    prompt_builder.build.return_value = "Constructed prompt"
    prompt_builder_cls.return_value = prompt_builder

    # AI
    report = {"summary": "AI diagnosis report"}
    ai = MagicMock()
    ai.analyze.return_value = report
    ai_cls.return_value = ai

    # Execute
    service = IncidentService()

    result = service.analyze("default", "my-pod")

    # Assert
    assert result == report

    kubernetes.collect.assert_called_once_with("default", "my-pod")
    metrics.collect.assert_called_once_with("default", "my-pod")
    prometheus.collect.assert_called_once_with("default", "my-pod")

    incident_builder.build.assert_called_once_with(
        kubernetes=kubernetes_snapshot,
        metrics=metrics_snapshot,
        prometheus=prometheus_snapshot,
    )

    engine.analyze.assert_called_once_with(incident)

    context_builder.build.assert_called_once_with(
        incident,
        findings,
    )

    prompt_builder.build.assert_called_once_with(context)

    ai.analyze.assert_called_once_with("Constructed prompt")
