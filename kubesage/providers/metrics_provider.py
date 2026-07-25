from typing import Protocol

from kubesage.models.metrics import PodMetrics


class MetricsProvider(Protocol):
    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> PodMetrics | None:
        """Collect metrics for a pod."""
        ...
