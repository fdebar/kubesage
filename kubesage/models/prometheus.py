from dataclasses import field
from datetime import datetime

from pydantic import BaseModel

from kubesage.models.container import ContainerUsage


class Metric(BaseModel):
    """Metric from Prometheus."""

    name: str
    value: float
    unit: str
    timestamp: float
    formatted_value: str | None = None


class MetricPoint(BaseModel):
    """A single time-series point from Prometheus."""

    timestamp: datetime
    value: float


class PrometheusResourceUsage(BaseModel):
    """Resource usage from Prometheus."""

    cpu: Metric | None = None
    memory: Metric | None = None
    cpu_throttling: Metric | None = None
    restarts: Metric | None = None

    network_rx: Metric | None = None
    network_tx: Metric | None = None

    filesystem: Metric | None = None

    request_rate: Metric | None = None
    error_rate: Metric | None = None
    latency: Metric | None = None

    containers: list[ContainerUsage] = field(default_factory=list)


class PrometheusTimeSeries(BaseModel):
    """A Prometheus time series."""

    name: str
    unit: str
    labels: dict[str, str]
    points: list[MetricPoint]


class RawPrometheusMetrics(BaseModel):
    """Raw metrics from Prometheus."""

    cpu: list = field(default_factory=list)
    memory: list = field(default_factory=list)
    container_cpu: list = field(default_factory=list)
    container_memory: list = field(default_factory=list)
    cpu_throttling: list = field(default_factory=list)
    restarts: list = field(default_factory=list)
    network_rx: list = field(default_factory=list)
    network_tx: list = field(default_factory=list)
    filesystem: list = field(default_factory=list)


class MetricChange(BaseModel):
    timestamp: datetime
    metric_name: str
    previous_value: float
    value: float
    change_ratio: float
    labels: dict[str, str]
