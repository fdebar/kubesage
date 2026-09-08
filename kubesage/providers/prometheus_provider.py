from datetime import datetime
from typing import Protocol

from kubesage.models.prometheus import PrometheusResourceUsage, PrometheusTimeSeries


class PrometheusProvider(Protocol):
    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> PrometheusResourceUsage:
        """Collect prometheus metrics for a pod."""
        ...

    def collect_time_series(
        self,
        namespace: str,
        pod: str,
        start: datetime,
        end: datetime,
        step: str,
    ) -> list[PrometheusTimeSeries]:
        """Collect prometheus time series for a pod."""
        ...
