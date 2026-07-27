from dataclasses import dataclass, field


@dataclass(slots=True)
class ContainerResources:
    """
    Kubernetes configured resources.
    Source: Kubernetes API.
    """

    name: str

    cpu_request: float | None = None
    cpu_limit: float | None = None

    memory_request: int | None = None
    memory_limit: int | None = None


@dataclass(slots=True)
class PodResources:
    containers: list[ContainerResources] = field(default_factory=list)
