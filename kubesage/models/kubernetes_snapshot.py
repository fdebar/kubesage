from pydantic import BaseModel, Field

from kubesage.models.container import ContainerStatus, PodResources
from kubesage.models.event import Event
from kubesage.models.log import LogSnapshot
from kubesage.models.prometheus import PrometheusResourceUsage


class KubernetesSnapshot(BaseModel):
    namespace: str
    pod: str
    phase: str
    logs: LogSnapshot
    pod_uid: str
    containers: list[ContainerStatus] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    metrics: PrometheusResourceUsage | None = None
    resources: PodResources = Field(default_factory=PodResources)
