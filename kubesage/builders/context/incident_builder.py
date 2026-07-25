from kubesage.models.incident import Incident
from kubesage.models.kubernetes import KubernetesSnapshot
from kubesage.models.log import LogSnapshot
from kubesage.models.metrics import PodMetrics
from kubesage.models.prometheus import ResourceUsage


class IncidentBuilder:
    def build(
        self,
        kubernetes: KubernetesSnapshot,
        prometheus: ResourceUsage | None = None,
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
