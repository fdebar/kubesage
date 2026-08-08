import structlog

from kubesage.builders.context.container_snapshot_builder import (
    ContainerSnapshotBuilder,
)
from kubesage.models.container import ContainerSnapshot
from kubesage.models.incident import Incident
from kubesage.models.kubernetes_snapshot import KubernetesSnapshot
from kubesage.models.log import LogSnapshot
from kubesage.models.metrics import PodMetrics
from kubesage.models.prometheus import PrometheusResourceUsage
from kubesage.providers.kubernetes_provider import KubernetesProvider
from kubesage.providers.log_provider import LogProvider
from kubesage.providers.metrics_provider import MetricsProvider
from kubesage.providers.prometheus_provider import PrometheusProvider

logger = structlog.get_logger()


class IncidentBuilder:
    def __init__(
        self,
        kubernetes_provider: KubernetesProvider,
        prometheus_provider: PrometheusProvider | None,
        metrics_provider: MetricsProvider,
        log_provider: LogProvider | None,
        container_snapshot_builder: ContainerSnapshotBuilder,
    ) -> None:
        self.kubernetes = kubernetes_provider
        self.prometheus_provider = prometheus_provider
        self.metrics = metrics_provider
        self.logs = log_provider
        self.container_snapshot_builder = container_snapshot_builder

    def collect(self, namespace: str, pod: str) -> Incident:
        kubernetes = self.kubernetes.collect(namespace, pod)
        metrics = self.metrics.collect(namespace, pod)

        prometheus: PrometheusResourceUsage | None = None
        if self.prometheus_provider is not None:
            prometheus = self.prometheus_provider.collect(namespace, pod)

        snapshots = self.container_snapshot_builder.build(
            statuses=kubernetes.containers,
            usages=prometheus.containers if prometheus else [],
            resources=kubernetes.resources,
        )

        loki_logs: LogSnapshot | None = None
        if self.logs is not None:
            loki_logs = self.logs.collect(namespace, pod)

        return self.build(
            kubernetes=kubernetes,
            containers=snapshots,
            prometheus=prometheus,
            loki_logs=loki_logs,
            container_metrics=metrics,
        )

    def build(
        self,
        kubernetes: KubernetesSnapshot,
        containers: list[ContainerSnapshot],
        prometheus: PrometheusResourceUsage | None = None,
        loki_logs: LogSnapshot | None = None,
        container_metrics: PodMetrics | None = None,
    ) -> Incident:
        return Incident(
            namespace=kubernetes.namespace,
            pod=kubernetes.pod,
            phase=kubernetes.phase,
            containers=containers,
            events=kubernetes.events,
            kubernetes_logs=kubernetes.logs,
            loki_logs=loki_logs,
            prometheus=prometheus,
            metrics=container_metrics,
        )
