from models.prometheus import ResourceUsage
from dataclasses import dataclass, field
from models.container import ContainerInfo
from models.metrics import PodMetrics
from models.events import Event


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
