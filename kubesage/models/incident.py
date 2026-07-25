from dataclasses import dataclass, field

from kubesage.models.container import ContainerInfo
from kubesage.models.events import Event
from kubesage.models.log import LogSnapshot, LogSource
from kubesage.models.metrics import PodMetrics
from kubesage.models.prometheus import ResourceUsage


@dataclass(slots=True)
class Incident:
    namespace: str
    pod: str
    phase: str
    events: list[Event] = field(default_factory=list)
    containers: list[ContainerInfo] = field(default_factory=list)
    metrics: PodMetrics | None = None
    log_source: LogSource = LogSource.KUBERNETES
    kubernetes_logs: LogSnapshot | None = None
    loki_logs: LogSnapshot | None = None
    prometheus: ResourceUsage | None = None

    @property
    def logs(self) -> str:
        """Preferred logs used by the AI."""
        if self.loki_logs:
            return self.loki_logs.content

        if self.kubernetes_logs:
            return self.kubernetes_logs.content

        return ""
