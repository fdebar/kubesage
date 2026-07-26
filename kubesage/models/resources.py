from dataclasses import dataclass, field


@dataclass(slots=True)
class ContainerResourceLimits:
    name: str

    cpu_limit: float | None = None
    memory_limit: int | None = None

    cpu_request: float | None = None
    memory_request: int | None = None


@dataclass(slots=True)
class PodResources:
    containers: list[ContainerResourceLimits] = field(default_factory=list)
