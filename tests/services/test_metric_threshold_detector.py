from datetime import UTC, datetime, timedelta

from kubesage.models.container import (
    ContainerResources,
    ContainerSnapshot,
)
from kubesage.models.prometheus import (
    MetricPoint,
    PrometheusTimeSeries,
)
from kubesage.services.metric_threshold_detector import (
    MetricThresholdDetector,
)


def _series(
    values: list[float],
    name: str = "container_cpu",
) -> PrometheusTimeSeries:
    start = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)

    return PrometheusTimeSeries(
        name=name,
        unit="cores",
        labels={"container": "web"},
        points=[
            MetricPoint(
                timestamp=start + timedelta(minutes=index),
                value=value,
            )
            for index, value in enumerate(values)
        ],
    )


def _container(
    cpu_limit: float | None = 1.0,
    memory_limit: int | None = 1_000,
) -> ContainerSnapshot:
    return ContainerSnapshot(
        name="web",
        image="nginx:latest",
        ready=True,
        restart_count=0,
        resources=ContainerResources(
            name="web",
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
        ),
    )


def test_detect_cpu_threshold_crossing() -> None:
    detector = MetricThresholdDetector()
    series = _series([0.50, 0.70, 0.79, 0.82, 0.90])
    changes = detector.detect_cpu(series=series, container=_container(cpu_limit=1.0))

    assert len(changes) == 1
    assert changes[0].previous_value == 0.79
    assert changes[0].value == 0.82
    assert changes[0].metric_name == "container_cpu"
    assert changes[0].labels == {"container": "web"}


def test_detect_cpu_does_not_repeat_while_above_threshold() -> None:
    detector = MetricThresholdDetector()
    series = _series([0.50, 0.82, 0.90, 0.95])
    changes = detector.detect_cpu(series=series, container=_container(cpu_limit=1.0))

    assert len(changes) == 1


def test_detect_cpu_detects_second_crossing_after_reset() -> None:
    detector = MetricThresholdDetector()
    series = _series([0.50, 0.82, 0.90, 0.70, 0.85])
    changes = detector.detect_cpu(series=series, container=_container(cpu_limit=1.0))

    assert len(changes) == 2
    assert changes[0].value == 0.82
    assert changes[1].value == 0.85


def test_detect_cpu_threshold_uses_container_limit() -> None:
    detector = MetricThresholdDetector()
    series = _series([0.30, 0.41])
    changes = detector.detect_cpu(series=series, container=_container(cpu_limit=0.5))

    assert len(changes) == 1
    assert changes[0].value == 0.41


def test_detect_cpu_returns_empty_without_cpu_limit() -> None:
    detector = MetricThresholdDetector()
    series = _series([0.50, 0.90])
    changes = detector.detect_cpu(
        series=series,
        container=_container(cpu_limit=None),
    )

    assert changes == []


def test_detect_memory_threshold_crossing() -> None:
    detector = MetricThresholdDetector()

    series = PrometheusTimeSeries(
        name="container_memory",
        unit="bytes",
        labels={"container": "web"},
        points=[
            MetricPoint(
                timestamp=datetime(2026, 8, 31, 10, index, tzinfo=UTC),
                value=value,
            )
            for index, value in enumerate([500, 700, 790, 810, 900])
        ],
    )

    changes = detector.detect_memory(
        series=series,
        container=_container(memory_limit=1_000),
    )

    assert len(changes) == 1
    assert changes[0].previous_value == 790
    assert changes[0].value == 810


def test_detect_throttling_threshold_crossing() -> None:
    detector = MetricThresholdDetector()
    series = _series([0.05, 0.10, 0.19, 0.25, 0.30], name="cpu_throttling")
    changes = detector.detect_throttling(series)

    assert len(changes) == 1
    assert changes[0].previous_value == 0.19
    assert changes[0].value == 0.25


def test_detect_throttling_resets_after_returning_below_threshold() -> None:
    detector = MetricThresholdDetector()
    series = _series([0.10, 0.25, 0.30, 0.10, 0.22], name="cpu_throttling")
    changes = detector.detect_throttling(series)

    assert len(changes) == 2


def test_detect_returns_empty_for_short_series() -> None:
    detector = MetricThresholdDetector()
    series = _series([0.90])
    changes = detector.detect_throttling(series)

    assert changes == []


def test_detect_cpu_returns_empty_for_invalid_limit() -> None:
    detector = MetricThresholdDetector()
    series = _series([0.10, 0.90])
    changes = detector.detect_cpu(series=series, container=_container(cpu_limit=0))

    assert changes == []
