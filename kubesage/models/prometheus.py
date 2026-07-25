from dataclasses import dataclass


@dataclass
class PrometheusSnapshot:
    cpu: float | None = None
    memory: float | None = None
    restarts: int | None = None

    network_rx: float | None = None
    network_tx: float | None = None

    filesystem_usage: float | None = None
    request_rate: float | None = None
    error_rate: float | None = None
    latency_p95: float | None = None


@dataclass(slots=True)
class Metric:
    name: str
    value: float
    unit: str
    timestamp: float


@dataclass(slots=True)
class ResourceUsage:
    cpu: Metric | None = None
    memory: Metric | None = None
    restarts: Metric | None = None
    network_rx: Metric | None = None
    network_tx: Metric | None = None
