from dataclasses import dataclass, field


@dataclass(slots=True)
class ContainerMetrics:
    """Represents the metrics of a container."""

    name: str
    cpu_usage: float | None = None
    memory_usage: int | None = None


@dataclass(slots=True)
class PodMetrics:
    """Represents the metrics of a pod."""

    containers: list[ContainerMetrics] = field(default_factory=list)
