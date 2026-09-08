from datetime import UTC, datetime, timedelta

import structlog

from kubesage.builders.context.container_snapshot_builder import (
    ContainerSnapshotBuilder,
)
from kubesage.models.incident import Incident
from kubesage.models.log import LogQueryType, LogSnapshot
from kubesage.models.prometheus import MetricChange, PrometheusResourceUsage
from kubesage.providers.kubernetes_provider import KubernetesProvider
from kubesage.providers.log_provider import LogProvider
from kubesage.providers.metrics_provider import MetricsProvider
from kubesage.providers.prometheus_provider import PrometheusProvider
from kubesage.services.metric_change_detector import MetricChangeDetector

logger = structlog.get_logger()


class IncidentBuilder:
    def __init__(
        self,
        kubernetes_provider: KubernetesProvider,
        prometheus_provider: PrometheusProvider | None,
        metrics_provider: MetricsProvider,
        log_provider: LogProvider | None,
    ) -> None:
        self.kubernetes_provider = kubernetes_provider
        self.prometheus_provider = prometheus_provider
        self.metrics_provider = metrics_provider
        self.log_provider = log_provider
        self.snapshot_builder = ContainerSnapshotBuilder()
        self.metric_change_detector = MetricChangeDetector()

    def collect(self, namespace: str, pod: str) -> Incident:
        prometheus: PrometheusResourceUsage | None = None
        metric_changes: list[MetricChange] = []
        observed_at = datetime.now(UTC)

        kubernetes = self.kubernetes_provider.collect(namespace, pod)
        metrics = self.metrics_provider.collect(namespace, pod)

        if self.prometheus_provider is not None:
            prometheus = self.prometheus_provider.collect(namespace, pod)
            start = observed_at - timedelta(minutes=5)
            time_series = self.prometheus_provider.collect_time_series(
                namespace=namespace,
                pod=pod,
                start=start,
                end=observed_at,
                step="30s",
            )

            for series in time_series:
                metric_changes.extend(self.metric_change_detector.detect(series))

        snapshots = self.snapshot_builder.build(
            statuses=kubernetes.containers,
            usages=prometheus.containers if prometheus else [],
            resources=kubernetes.resources,
        )

        loki_logs: LogSnapshot | None = None
        if self.log_provider is not None:
            loki_logs = self.log_provider.collect(
                namespace, pod, query_type=LogQueryType.ALL
            )

        return Incident(
            namespace=kubernetes.namespace,
            pod=kubernetes.pod,
            pod_uid=kubernetes.pod_uid,
            phase=kubernetes.phase,
            observed_at=observed_at,
            containers=snapshots,
            events=kubernetes.events,
            kubernetes_logs=kubernetes.logs,
            loki_logs=loki_logs,
            prometheus=prometheus,
            metrics=metrics,
            metric_changes=metric_changes,
        )
