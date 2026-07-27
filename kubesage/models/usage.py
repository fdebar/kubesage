from dataclasses import dataclass


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
