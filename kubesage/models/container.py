from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ContainerUsage:
    """
    Runtime container consumption metrics.
    Source: Prometheus.
    """

    name: str
    cpu_usage: float | None = None
    memory_usage: int | None = None
    cpu_throttling_ratio: float | None = None


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


@dataclass(slots=True)
class ContainerSnapshot:
    """
    Complete container state.
    """

    name: str
    image: str
    ready: bool
    restart_count: int

    waiting_reason: str | None = None
    waiting_message: str | None = None

    last_exit_code: int | None = None
    last_exit_reason: str | None = None

    resources: ContainerResources | None = None
    usage: ContainerUsage | None = None


@dataclass(slots=True)
class ContainerStatus:
    """
    Container state used for incident reporting.
    """

    name: str
    image: str
    ready: bool
    restart_count: int

    waiting_reason: str | None = None
    waiting_message: str | None = None

    last_exit_code: int | None = None
    last_exit_reason: str | None = None

    started_at: datetime | None = None
    finished_at: datetime | None = None
