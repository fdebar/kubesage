from unittest.mock import MagicMock, patch

from kubesage.services.incident_service import IncidentService


@patch("kubesage.services.incident_service.KubernetesService")
@patch("kubesage.services.incident_service.MetricsService")
@patch("kubesage.services.incident_service.PrometheusService")
@patch("kubesage.services.incident_service.DiagnosticEngine")
@patch("kubesage.services.incident_service.ContextBuilder")
@patch("kubesage.services.incident_service.PromptBuilder")
@patch("kubesage.services.incident_service.AIService")
def test_analyze_flow(
    mock_ai_class: MagicMock,
    mock_prompt_builder_class: MagicMock,
    mock_context_builder_class: MagicMock,
    mock_engine_class: MagicMock,
    mock_prometheus_class: MagicMock,
    mock_metrics_class: MagicMock,
    mock_kubernetes_class: MagicMock,
) -> None:
    mock_kubernetes = MagicMock()
    mock_incident = MagicMock()
    mock_kubernetes.collect.return_value = mock_incident
    mock_kubernetes_class.return_value = mock_kubernetes

    mock_metrics = MagicMock()
    mock_metrics_data = MagicMock()
    mock_metrics.collect.return_value = mock_metrics_data
    mock_metrics_class.return_value = mock_metrics

    mock_prometheus = MagicMock()
    mock_prom_data = MagicMock()
    mock_prometheus.collect.return_value = mock_prom_data
    mock_prometheus_class.return_value = mock_prometheus

    mock_engine = MagicMock()
    mock_findings = ["finding1", "finding2"]
    mock_engine.analyze.return_value = mock_findings
    mock_engine_class.return_value = mock_engine

    mock_context_builder = MagicMock()
    mock_ctx = MagicMock()
    mock_context_builder.build.return_value = mock_ctx
    mock_context_builder_class.return_value = mock_context_builder

    mock_prompt_builder = MagicMock()
    mock_prompt_builder.build.return_value = "Constructed prompt"
    mock_prompt_builder_class.return_value = mock_prompt_builder

    mock_ai = MagicMock()
    mock_report = {"summary": "AI diagnosis report"}
    mock_ai.analyze.return_value = mock_report
    mock_ai_class.return_value = mock_ai

    service = IncidentService()

    report = service.analyze("default", "my-pod")

    assert report == mock_report
    mock_kubernetes.collect.assert_called_once_with("default", "my-pod")
    mock_metrics.collect.assert_called_once_with("default", "my-pod")
    mock_prometheus.collect.assert_called_once_with("default", "my-pod")
    mock_engine.analyze.assert_called_once_with(mock_incident)
    mock_context_builder.build.assert_called_once_with(mock_incident, mock_findings)
    mock_prompt_builder.build.assert_called_once_with(mock_ctx)
    mock_ai.analyze.assert_called_once_with("Constructed prompt")

    # Assert metrics and prometheus were attached to the incident
    assert mock_incident.metrics == mock_metrics_data
    assert mock_incident.prometheus == mock_prom_data
