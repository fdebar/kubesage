from kubesage.models.prometheus import MetricChange, PrometheusTimeSeries


class MetricChangeDetector:
    """Detects significant changes in Prometheus time series."""

    def detect(
        self,
        series: PrometheusTimeSeries,
        relative_threshold: float = 1.0,
    ) -> list[MetricChange]:
        changes: list[MetricChange] = []
        active = False

        for previous, current in zip(series.points, series.points[1:], strict=True):
            if previous.value == 0:
                continue

            change_ratio = (current.value - previous.value) / abs(previous.value)
            significant = abs(change_ratio) >= relative_threshold
            if significant and not active:
                changes.append(
                    MetricChange(
                        timestamp=current.timestamp,
                        metric_name=series.name,
                        previous_value=previous.value,
                        value=current.value,
                        change_ratio=change_ratio,
                        labels=series.labels,
                    )
                )

            active = significant

        return changes
