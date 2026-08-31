from itertools import pairwise

from kubesage.models.container import ContainerSnapshot
from kubesage.models.prometheus import MetricChange, PrometheusTimeSeries


class MetricThresholdDetector:
    """Detect threshold crossings in container Prometheus time series."""

    CPU_THRESHOLD = 0.80
    MEMORY_THRESHOLD = 0.80
    THROTTLING_THRESHOLD = 0.20

    def detect_cpu(
        self,
        series: PrometheusTimeSeries,
        container: ContainerSnapshot,
    ) -> list[MetricChange]:
        if (
            container.resources is None
            or container.resources.cpu_limit is None
            or container.resources.cpu_limit <= 0
        ):
            return []

        return self._detect_threshold_crossings(
            series=series,
            threshold=container.resources.cpu_limit * self.CPU_THRESHOLD,
        )

    def detect_memory(
        self,
        series: PrometheusTimeSeries,
        container: ContainerSnapshot,
    ) -> list[MetricChange]:
        if (
            container.resources is None
            or container.resources.memory_limit is None
            or container.resources.memory_limit <= 0
        ):
            return []

        return self._detect_threshold_crossings(
            series=series,
            threshold=container.resources.memory_limit * self.MEMORY_THRESHOLD,
        )

    def detect_throttling(self, series: PrometheusTimeSeries) -> list[MetricChange]:
        return self._detect_threshold_crossings(
            series=series,
            threshold=self.THROTTLING_THRESHOLD,
        )

    @staticmethod
    def _detect_threshold_crossings(
        series: PrometheusTimeSeries,
        threshold: float,
    ) -> list[MetricChange]:
        if len(series.points) < 2:
            return []

        changes: list[MetricChange] = []
        was_above = series.points[0].value >= threshold

        for previous, current in pairwise(series.points):
            is_above = current.value >= threshold

            if is_above and not was_above:
                changes.append(
                    MetricChange(
                        timestamp=current.timestamp,
                        metric_name=series.name,
                        previous_value=previous.value,
                        value=current.value,
                        labels=series.labels,
                    )
                )

            was_above = is_above

        return changes
