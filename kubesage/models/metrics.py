from dataclasses import dataclass, field


@dataclass(slots=True)
class ContainerMetrics:
    name: str
    cpu: str
    memory: str


@dataclass(slots=True)
class PodMetrics:
    containers: list[ContainerMetrics] = field(default_factory=list)
