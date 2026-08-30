from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from kubesage.models.finding import ResourceRef, Severity


class TimelineEventType(StrEnum):
    DEPLOYMENT = "deployment"
    KUBERNETES_EVENT = "kubernetes_event"
    CONTAINER_STARTED = "container_started"
    CONTAINER_TERMINATED = "container_terminated"
    POD_RESTART = "pod_restart"
    METRIC_ANOMALY = "metric_anomaly"
    LOG_EVENT = "log_event"
    TRACE_EVENT = "trace_event"
    FINDING = "finding"
    ANALYSIS = "analysis"
    METRIC_CHANGE = "metric_change"


class TimelineEventSource(StrEnum):
    KUBERNETES = "kubernetes"
    PROMETHEUS = "prometheus"
    LOKI = "loki"
    TEMPO = "tempo"
    KUBESAGE = "kubesage"


class TimelineEvent(BaseModel):
    id: str
    timestamp: datetime
    type: TimelineEventType
    source: TimelineEventSource
    title: str
    description: str | None = None
    severity: Severity = Severity.INFO
    resource: ResourceRef | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
