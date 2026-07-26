from dataclasses import dataclass, field


@dataclass(slots=True)
class ContainerMetrics:
    name: str

    cpu_usage: float | None = None
    memory_usage: int | None = None

    cpu_limit: float | None = None
    memory_limit: int | None = None

    cpu_throttling_ratio: float | None = None


@dataclass(slots=True)
class PodMetrics:
    containers: list[ContainerMetrics] = field(default_factory=list)
