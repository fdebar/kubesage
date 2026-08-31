from kubesage.models.prometheus import MetricChange, PrometheusTimeSeries


class MetricChangeDetector:
    """Detects significant changes in Prometheus time series."""

    def detect(
        self,
        series: PrometheusTimeSeries,
        relative_threshold: float = 1.0,
    ) -> list[MetricChange]:
        changes: list[MetricChange] = []

        for previous, current in zip(series.points, series.points[1:], strict=True):
            if previous.value == 0:
                continue

            changes.append(
                MetricChange(
                    timestamp=current.timestamp,
                    metric_name=series.name,
                    previous_value=previous.value,
                    value=current.value,
                    labels=series.labels,
                )
            )

        return changes
