from datetime import UTC, datetime
from unittest.mock import MagicMock

from kubesage.builders.context.incident_builder import IncidentBuilder
from kubesage.models.container import PodResources
from kubesage.models.prometheus import (
    MetricPoint,
    PrometheusResourceUsage,
    PrometheusTimeSeries,
)


def test_collect_adds_metric_changes_to_incident() -> None:
    kubernetes_provider = MagicMock()
    prometheus_provider = MagicMock()
    metrics_provider = MagicMock()
    log_provider = MagicMock()

    kubernetes = MagicMock()
    kubernetes.namespace = "monitoring"
    kubernetes.pod = "grafana"
    kubernetes.pod_uid = "pod-uid"
    kubernetes.phase = "Running"
    kubernetes.containers = []
    kubernetes.resources = PodResources(containers=[])
    kubernetes.events = []
    kubernetes.logs = None

    kubernetes_provider.collect.return_value = kubernetes
    prometheus_provider.collect.return_value = PrometheusResourceUsage(containers=[])
    metrics_provider.collect.return_value = None
    log_provider.collect.return_value = None

    time_series = [
        PrometheusTimeSeries(
            name="memory",
            unit="bytes",
            labels={
                "namespace": "monitoring",
                "pod": "grafana",
                "container": "grafana",
            },
            points=[
                MetricPoint(
                    timestamp=datetime(2026, 9, 8, 15, 0, tzinfo=UTC),
                    value=500.0,
                ),
                MetricPoint(
                    timestamp=datetime(2026, 9, 8, 15, 0, 30, tzinfo=UTC),
                    value=600.0,
                ),
            ],
        )
    ]

    prometheus_provider.collect_time_series.return_value = time_series

    builder = IncidentBuilder(
        kubernetes_provider=kubernetes_provider,
        prometheus_provider=prometheus_provider,
        metrics_provider=metrics_provider,
        log_provider=log_provider,
    )

    incident = builder.collect(namespace="monitoring", pod="grafana")

    assert len(incident.metric_changes) == 1

    change = incident.metric_changes[0]
    assert change.metric_name == "memory"
    assert change.previous_value == 500.0
    assert change.value == 600.0
    assert change.labels == {
        "namespace": "monitoring",
        "pod": "grafana",
        "container": "grafana",
    }

    prometheus_provider.collect_time_series.assert_called_once()
