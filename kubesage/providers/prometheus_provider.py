from typing import Protocol

from kubesage.models.prometheus import PrometheusResourceUsage


class PrometheusProvider(Protocol):
    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> PrometheusResourceUsage | None:
        """Collect prometheus metrics for a pod."""
        ...
