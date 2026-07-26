from dataclasses import dataclass, field

from kubesage.models.metrics import ContainerMetrics


@dataclass(slots=True)
class Metric:
    name: str
    value: float
    unit: str
    timestamp: float
    formatted_value: str | None = None


@dataclass(slots=True)
class PrometheusResourceUsage:
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

    containers: list[ContainerMetrics] = field(default_factory=list)
