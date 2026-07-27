from pydantic import BaseModel, Field

from kubesage.models.container import ContainerInfo
from kubesage.models.events import Event
from kubesage.models.log import LogSnapshot
from kubesage.models.prometheus import PrometheusResourceUsage
from kubesage.models.resources import PodResources


class KubernetesSnapshot(BaseModel):
    namespace: str
    pod: str
    phase: str
    logs: LogSnapshot

    containers: list[ContainerInfo] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)

    metrics: PrometheusResourceUsage | None = None
    resources: PodResources | None = None
