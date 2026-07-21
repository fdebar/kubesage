from models.prometheus import ResourceUsage
from dataclasses import dataclass, field
from models.container import ContainerInfo
from models.metrics import PodMetrics


@dataclass(slots=True)
class Incident:

    namespace: str
    pod: str
    phase: str
    logs: str
    containers: list[ContainerInfo]
    events: list[dict] = field(default_factory=list)
    metrics: PodMetrics | None = None
    prometheus: ResourceUsage | None = None
