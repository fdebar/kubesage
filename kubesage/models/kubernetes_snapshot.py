from dataclasses import dataclass, field

from kubesage.models.container import ContainerInfo
from kubesage.models.events import Event
from kubesage.models.log import LogSnapshot
from kubesage.models.metrics import PodMetrics


@dataclass(slots=True)
class KubernetesSnapshot:
    namespace: str
    pod: str
    phase: str
    logs: LogSnapshot
    containers: list[ContainerInfo] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    metrics: PodMetrics | None = None
