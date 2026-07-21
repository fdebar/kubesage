from dataclasses import dataclass


@dataclass(slots=True)
class Metric:
    name: str
    value: float
    unit: str


@dataclass(slots=True)
class ResourceUsage:
    cpu: Metric | None = None
    memory: Metric | None = None
    restarts: Metric | None = None
    network_rx: Metric | None = None
    network_tx: Metric | None = None
