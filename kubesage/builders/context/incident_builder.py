from kubesage.models.incident import Incident
from kubesage.models.kubernetes import KubernetesSnapshot
from kubesage.models.log import LogSnapshot
from kubesage.models.metrics import PodMetrics
from kubesage.models.prometheus import PrometheusResourceUsage
from kubesage.providers.kubernetes_provider import KubernetesProvider
from kubesage.providers.log_provider import LogProvider
from kubesage.providers.metrics_provider import MetricsProvider
from kubesage.providers.prometheus_provider import PrometheusProvider


class IncidentBuilder:
    def __init__(
        self,
        kubernetes_provider: KubernetesProvider,
        prometheus_provider: PrometheusProvider,
        metrics_provider: MetricsProvider,
        log_provider: LogProvider,
    ) -> None:
        self.kubernetes = kubernetes_provider
        self.prometheus = prometheus_provider
        self.metrics = metrics_provider
        self.logs = log_provider

    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> Incident:
        kubernetes = self.kubernetes.collect(namespace, pod)
        prometheus = self.prometheus.collect(namespace, pod)
        metrics = self.metrics.collect(namespace, pod)

        if self.logs is not None:
            loki_logs = self.logs.collect(namespace, pod)

        return self.build(
            kubernetes=kubernetes,
            prometheus=prometheus,
            loki_logs=loki_logs,
            metrics=metrics,
        )

    def build(
        self,
        kubernetes: KubernetesSnapshot,
        prometheus: PrometheusResourceUsage | None = None,
        loki_logs: LogSnapshot | None = None,
        metrics: PodMetrics | None = None,
    ) -> Incident:
        return Incident(
            namespace=kubernetes.namespace,
            pod=kubernetes.pod,
            phase=kubernetes.phase,
            containers=kubernetes.containers,
            events=kubernetes.events,
            kubernetes_logs=kubernetes.logs,
            loki_logs=loki_logs,
            prometheus=prometheus,
            metrics=metrics,
        )
