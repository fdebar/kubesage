from dataclasses import dataclass

from kubesage.models.container import ContainerInfo
from kubesage.models.events import Event
from kubesage.models.metrics import PodMetrics
from kubesage.models.prometheus import ResourceUsage


@dataclass(slots=True)
class Incident:
    namespace: str
    pod: str
    phase: str
    logs: str
    containers: list[ContainerInfo]
    events: list[Event]
    metrics: PodMetrics | None = None
    prometheus: ResourceUsage | None = None
