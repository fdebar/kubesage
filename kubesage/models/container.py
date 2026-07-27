from dataclasses import dataclass

from kubesage.models.resources import ContainerResources
from kubesage.models.usage import ContainerUsage


@dataclass(slots=True)
class ContainerSnapshot:
    """
    Complete container state.
    """

    # Identity
    name: str

    # Kubernetes state
    image: str
    ready: bool
    restart_count: int

    waiting_reason: str | None = None
    waiting_message: str | None = None

    last_exit_code: int | None = None
    last_exit_reason: str | None = None

    # Kubernetes configuration
    resources: ContainerResources | None = None

    # Runtime observations
    usage: ContainerUsage | None = None


@dataclass(slots=True)
class ContainerStatus:
    name: str
    image: str
    ready: bool
    restart_count: int

    waiting_reason: str | None = None
    waiting_message: str | None = None

    last_exit_code: int | None = None
    last_exit_reason: str | None = None
