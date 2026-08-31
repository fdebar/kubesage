from datetime import UTC, datetime

from kubesage.builders.timeline import TimelineBuilder
from kubesage.models.container import ContainerSnapshot
from kubesage.models.event import Event
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry, LogSnapshot, LogSource
from kubesage.models.prometheus import MetricChange
from kubesage.models.timeline import (
    Severity,
    TimelineEventSource,
    TimelineEventType,
)


def _incident(*, loki_logs: LogSnapshot | None = None) -> Incident:
    return Incident(
        namespace="default",
        pod="kubesage-api",
        pod_uid="pod-uid",
        phase="Running",
        observed_at=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
        loki_logs=loki_logs,
    )


def test_build_includes_loki_error_log() -> None:
    timestamp = datetime(2026, 8, 31, 10, 5, tzinfo=UTC)

    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=timestamp,
                    message="ERROR database connection refused",
                    labels={
                        "namespace": "default",
                        "pod": "kubesage-api",
                    },
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1

    event = events[0]
    assert event.type == TimelineEventType.LOG_EVENT
    assert event.source == TimelineEventSource.LOKI
    assert event.timestamp == timestamp
    assert event.title == "Application error"
    assert event.description == "ERROR database connection refused"
    assert event.severity == Severity.ERROR
    assert event.resource is not None
    assert event.resource.api_version == "v1"
    assert event.resource.kind == "Pod"
    assert event.resource.namespace == "default"
    assert event.resource.name == "kubesage-api"
    assert event.metadata == {
        "labels": {
            "namespace": "default",
            "pod": "kubesage-api",
        },
    }


def test_build_includes_loki_warning_log() -> None:
    timestamp = datetime(2026, 8, 31, 10, 6, tzinfo=UTC)

    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=timestamp,
                    message="WARNING retrying database connection",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1

    event = events[0]
    assert event.type == TimelineEventType.LOG_EVENT
    assert event.source == TimelineEventSource.LOKI
    assert event.timestamp == timestamp
    assert event.title == "Application warning"
    assert event.description == "WARNING retrying database connection"
    assert event.severity == Severity.WARNING


def test_build_includes_fatal_loki_log_as_error() -> None:
    timestamp = datetime(2026, 8, 31, 10, 7, tzinfo=UTC)

    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=timestamp,
                    message="FATAL application crashed",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1
    assert events[0].severity == Severity.ERROR
    assert events[0].type == TimelineEventType.LOG_EVENT
    assert events[0].source == TimelineEventSource.LOKI


def test_build_includes_critical_loki_log_as_error() -> None:
    timestamp = datetime(2026, 8, 31, 10, 8, tzinfo=UTC)

    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=timestamp,
                    message="CRITICAL unable to start application",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1
    assert events[0].severity == Severity.ERROR


def test_build_includes_warn_loki_log() -> None:
    timestamp = datetime(2026, 8, 31, 10, 9, tzinfo=UTC)

    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=timestamp,
                    message="WARN connection retry",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1
    assert events[0].severity == Severity.WARNING
    assert events[0].title == "Application warning"


def test_build_ignores_loki_info_logs() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
                    message="INFO application started",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert events == []


def test_build_ignores_loki_debug_logs() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
                    message="DEBUG loading configuration",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert events == []


def test_build_ignores_loki_trace_logs() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
                    message="TRACE entering handler",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert events == []


def test_build_sorts_loki_events_chronologically() -> None:
    early = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)
    late = datetime(2026, 8, 31, 10, 10, tzinfo=UTC)

    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=late,
                    message="ERROR late error",
                ),
                LogEntry(
                    timestamp=early,
                    message="ERROR early error",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert [event.timestamp for event in events] == [early, late]


def test_build_preserves_loki_labels() -> None:
    timestamp = datetime(2026, 8, 31, 10, 5, tzinfo=UTC)

    labels = {
        "namespace": "default",
        "pod": "kubesage-api",
        "container": "api",
    }

    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=timestamp,
                    message="ERROR request failed",
                    labels=labels,
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert events[0].metadata == {"labels": labels}


def test_build_without_loki_logs_returns_no_loki_events() -> None:
    incident = _incident(loki_logs=None)

    events = TimelineBuilder().build(incident)
    assert events == []


def test_build_ignores_unrecognized_log_level() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
                    message="application failed unexpectedly",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert events == []


def test_build_handles_multiple_loki_events() -> None:
    first = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)
    second = datetime(2026, 8, 31, 10, 1, tzinfo=UTC)
    third = datetime(2026, 8, 31, 10, 2, tzinfo=UTC)

    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=first,
                    message="INFO application started",
                ),
                LogEntry(
                    timestamp=second,
                    message="WARNING connection slow",
                ),
                LogEntry(
                    timestamp=third,
                    message="ERROR connection failed",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)

    assert len(events) == 2

    assert events[0].timestamp == second
    assert events[0].severity == Severity.WARNING

    assert events[1].timestamp == third
    assert events[1].severity == Severity.ERROR


def test_build_merges_all_event_sources_chronologically() -> None:
    kubernetes_timestamp = datetime(2026, 8, 31, 10, 2, tzinfo=UTC)
    container_timestamp = datetime(2026, 8, 31, 10, 4, tzinfo=UTC)
    metric_timestamp = datetime(2026, 8, 31, 10, 6, tzinfo=UTC)
    log_timestamp = datetime(2026, 8, 31, 10, 8, tzinfo=UTC)

    incident = Incident(
        namespace="default",
        pod="kubesage-api",
        pod_uid="pod-uid",
        phase="Running",
        observed_at=datetime(2026, 8, 31, 10, 10, tzinfo=UTC),
        events=[
            Event(
                type="Normal",
                reason="Started",
                message="Pod started",
                last_timestamp=kubernetes_timestamp,
            ),
        ],
        containers=[
            ContainerSnapshot(
                name="api",
                image="api:latest",
                ready=True,
                restart_count=0,
                started_at=container_timestamp,
            ),
        ],
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=log_timestamp,
                    message="ERROR database unavailable",
                ),
            ],
        ),
    )

    metric_change = MetricChange(
        metric_name="cpu",
        previous_value=0.2,
        value=0.8,
        timestamp=metric_timestamp,
        labels={},
    )
    events = TimelineBuilder().build(incident, metric_changes=[metric_change])

    assert len(events) == 4
    assert [event.timestamp for event in events] == [
        kubernetes_timestamp,
        container_timestamp,
        metric_timestamp,
        log_timestamp,
    ]
    assert [event.source for event in events] == [
        TimelineEventSource.KUBERNETES,
        TimelineEventSource.KUBERNETES,
        TimelineEventSource.PROMETHEUS,
        TimelineEventSource.LOKI,
    ]


def test_build_sorts_events_across_sources() -> None:
    early = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)
    middle = datetime(2026, 8, 31, 10, 5, tzinfo=UTC)
    late = datetime(2026, 8, 31, 10, 10, tzinfo=UTC)

    incident = Incident(
        namespace="default",
        pod="kubesage-api",
        pod_uid="pod-uid",
        phase="Running",
        observed_at=middle,
        events=[
            Event(
                type="Normal",
                reason="Late",
                message="Late event",
                last_timestamp=late,
            ),
        ],
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=early,
                    message="ERROR early error",
                ),
            ],
        ),
    )

    metric_change = MetricChange(
        metric_name="cpu",
        previous_value=0.2,
        value=0.8,
        timestamp=middle,
        labels={},
    )

    events = TimelineBuilder().build(incident, metric_changes=[metric_change])
    assert [event.timestamp for event in events] == [early, middle, late]


def test_build_handles_incident_without_optional_sources() -> None:
    incident = Incident(
        namespace="default",
        pod="kubesage-api",
        pod_uid="pod-uid",
        phase="Running",
        observed_at=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
    )

    events = TimelineBuilder().build(incident)
    assert events == []


def test_build_without_metric_changes_still_builds_loki_events() -> None:
    timestamp = datetime(2026, 8, 31, 10, 5, tzinfo=UTC)
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=timestamp,
                    message="ERROR database unavailable",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)

    assert len(events) == 1
    assert events[0].timestamp == timestamp
    assert events[0].source == TimelineEventSource.LOKI
