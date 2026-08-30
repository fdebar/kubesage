from datetime import datetime

from pydantic import BaseModel, Field

from kubesage.models.container import ContainerSnapshot
from kubesage.models.event import Event
from kubesage.models.log import LogSnapshot, LogSource
from kubesage.models.metrics import PodMetrics
from kubesage.models.prometheus import PrometheusResourceUsage


class Incident(BaseModel):
    namespace: str
    pod: str
    pod_uid: str | None = None
    phase: str
    observed_at: datetime
    events: list[Event] = Field(default_factory=list)
    containers: list[ContainerSnapshot] = Field(default_factory=list)
    metrics: PodMetrics | None = None
    log_source: LogSource = LogSource.KUBERNETES
    kubernetes_logs: LogSnapshot | None = None
    loki_logs: LogSnapshot | None = None
    prometheus: PrometheusResourceUsage | None = None

    @property
    def logs(self) -> str:
        """Preferred logs used by the AI."""

        if self.loki_logs:
            return self.loki_logs.content

        if self.kubernetes_logs:
            return self.kubernetes_logs.content

        return ""
