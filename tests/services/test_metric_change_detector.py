from datetime import UTC, datetime, timedelta

from kubesage.models.prometheus import MetricPoint, PrometheusTimeSeries
from kubesage.services.metric_change_detector import MetricChangeDetector


def _series(values: list[float]) -> PrometheusTimeSeries:
    start = datetime(2026, 9, 8, 15, 0, tzinfo=UTC)

    return PrometheusTimeSeries(
        name="memory",
        unit="bytes",
        labels={
            "namespace": "monitoring",
            "pod": "grafana",
            "container": "grafana",
        },
        points=[
            MetricPoint(
                timestamp=start + timedelta(seconds=index * 30),
                value=value,
            )
            for index, value in enumerate(values)
        ],
    )


def test_detects_significant_increase() -> None:
    detector = MetricChangeDetector()
    changes = detector.detect(_series([100.0, 120.0]), relative_threshold=0.1)

    assert len(changes) == 1

    change = changes[0]
    assert change.metric_name == "memory"
    assert change.previous_value == 100.0
    assert change.value == 120.0
    assert change.labels["container"] == "grafana"


def test_detects_significant_decrease() -> None:
    detector = MetricChangeDetector()
    changes = detector.detect(_series([100.0, 50.0]), relative_threshold=0.1)

    assert len(changes) == 1

    change = changes[0]
    assert change.previous_value == 100.0
    assert change.value == 50.0


def test_ignores_change_below_relative_threshold() -> None:
    detector = MetricChangeDetector()
    changes = detector.detect(_series([100.0, 105.0]), relative_threshold=0.1)

    assert changes == []


def test_detects_multiple_significant_changes() -> None:
    detector = MetricChangeDetector()
    changes = detector.detect(_series([100.0, 120.0, 150.0]), relative_threshold=0.1)

    assert len(changes) == 2

    assert changes[0].previous_value == 100.0
    assert changes[0].value == 120.0

    assert changes[1].previous_value == 120.0
    assert changes[1].value == 150.0


def test_ignores_transition_from_zero() -> None:
    detector = MetricChangeDetector()
    changes = detector.detect(_series([0.0, 100.0]), relative_threshold=0.1)

    assert changes == []


def test_returns_empty_for_single_point() -> None:
    detector = MetricChangeDetector()
    changes = detector.detect(_series([100.0]), relative_threshold=0.1)

    assert changes == []


def test_preserves_timestamp_from_current_point() -> None:
    detector = MetricChangeDetector()
    series = _series([100.0, 120.0])
    changes = detector.detect(series, relative_threshold=0.1)

    assert len(changes) == 1
    assert changes[0].timestamp == series.points[1].timestamp


def test_preserves_series_metadata() -> None:
    detector = MetricChangeDetector()
    changes = detector.detect(_series([100.0, 120.0]), relative_threshold=0.1)

    assert len(changes) == 1
    assert changes[0].metric_name == "memory"
    assert changes[0].labels == {
        "namespace": "monitoring",
        "pod": "grafana",
        "container": "grafana",
    }
