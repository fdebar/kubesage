from datetime import UTC, datetime

from kubesage.builders.timeline import TimelineBuilder
from kubesage.models.container import ContainerSnapshot
from kubesage.models.event import Event
from kubesage.models.finding import Severity
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry, LogSnapshot, LogSource
from kubesage.models.prometheus import MetricChange
from kubesage.models.timeline import (
    TimelineEventSource,
    TimelineEventType,
)


def _incident(
    *,
    events: list[Event] | None = None,
    containers: list[ContainerSnapshot] | None = None,
    loki_logs: LogSnapshot | None = None,
) -> Incident:
    return Incident(
        namespace="default",
        pod="kubesage-api",
        pod_uid="pod-uid",
        phase="Running",
        observed_at=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
        loki_logs=loki_logs,
        events=events or [],
        containers=containers or [],
    )


def test_build_returns_empty_timeline_for_empty_incident() -> None:
    incident = _incident()

    events = TimelineBuilder().build(incident)

    assert events == []


def test_build_includes_kubernetes_event() -> None:
    timestamp = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)

    incident = _incident(
        events=[
            Event(
                type="Warning",
                reason="BackOff",
                message="Back-off restarting failed container",
                last_timestamp=timestamp,
            )
        ],
    )

    events = TimelineBuilder().build(incident)

    assert len(events) == 1

    event = events[0]

    assert event.type == TimelineEventType.KUBERNETES_EVENT
    assert event.source == TimelineEventSource.KUBERNETES
    assert event.timestamp == timestamp
    assert event.title == "BackOff"
    assert event.description == "Back-off restarting failed container"
    assert event.severity == Severity.WARNING
    assert event.resource is not None
    assert event.resource.api_version == "v1"
    assert event.resource.kind == "Pod"
    assert event.resource.namespace == "default"
    assert event.resource.name == "kubesage-api"
    assert event.metadata == {
        "event_type": "Warning",
        "reason": "BackOff",
    }


def test_build_includes_container_started_event() -> None:
    timestamp = datetime(2026, 8, 31, 10, 1, tzinfo=UTC)

    incident = _incident(
        containers=[
            ContainerSnapshot(
                name="api",
                started_at=timestamp,
                ready=True,
                image="image",
                restart_count=0,
            )
        ],
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1

    event = events[0]
    assert event.type == TimelineEventType.CONTAINER_STARTED
    assert event.source == TimelineEventSource.KUBERNETES
    assert event.timestamp == timestamp
    assert event.title == "Container started"
    assert event.description == "Container 'api' started."
    assert event.severity == Severity.INFO
    assert event.resource is not None
    assert event.resource.kind == "Pod"
    assert event.metadata == {
        "container": "api",
    }


def test_build_includes_container_terminated_event() -> None:
    timestamp = datetime(2026, 8, 31, 10, 2, tzinfo=UTC)

    incident = _incident(
        containers=[
            ContainerSnapshot(
                name="api",
                finished_at=timestamp,
                last_exit_code=1,
                last_exit_reason="Error",
                ready=False,
                image="image",
                restart_count=0,
            )
        ],
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1

    event = events[0]
    assert event.type == TimelineEventType.CONTAINER_TERMINATED
    assert event.source == TimelineEventSource.KUBERNETES
    assert event.timestamp == timestamp
    assert event.title == "Container terminated"
    assert event.description == "Container 'api' terminated: Error."
    assert event.severity == Severity.ERROR
    assert event.metadata == {
        "container": "api",
        "exit_code": 1,
        "reason": "Error",
    }


def test_build_includes_metric_change() -> None:
    timestamp = datetime(2026, 8, 31, 10, 3, tzinfo=UTC)

    incident = _incident()

    metric_change = MetricChange(
        metric_name="container_cpu_usage",
        previous_value=0.2,
        value=0.8,
        timestamp=timestamp,
        labels={
            "namespace": "default",
            "pod": "kubesage-api",
        },
    )

    events = TimelineBuilder().build(incident, metric_changes=[metric_change])
    assert len(events) == 1

    event = events[0]
    assert event.type == TimelineEventType.METRIC_CHANGE
    assert event.source == TimelineEventSource.PROMETHEUS
    assert event.timestamp == timestamp
    assert event.title == "container_cpu_usage increased"
    assert event.description == "container_cpu_usage increased from 0.2 to 0.8."
    assert event.severity == Severity.INFO
    assert event.metadata == {
        "metric": "container_cpu_usage",
        "previous_value": 0.2,
        "value": 0.8,
        "labels": {
            "namespace": "default",
            "pod": "kubesage-api",
        },
    }


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
        "error_kind": "connection_error",
        "error_domain": "database",
    }


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
    assert len(events) == 1
    assert events[0].metadata == {
        "labels": labels,
        "error_kind": "generic_error",
    }


def test_build_preserves_loki_labels_with_existing_error_kind_label() -> None:
    timestamp = datetime(2026, 8, 31, 10, 5, tzinfo=UTC)

    labels = {
        "namespace": "default",
        "pod": "kubesage-api",
        "container": "api",
        "error_kind": "generic_error",
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
    assert events[0].metadata["labels"] == labels
    assert events[0].metadata["error_kind"] == "generic_error"


def test_loki_application_error_is_classified() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 5, tzinfo=UTC),
                    message="ERROR database connection refused",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    log_events = [event for event in events if event.source == TimelineEventSource.LOKI]
    assert len(log_events) == 1

    event = log_events[0]
    assert event.severity == Severity.ERROR
    assert event.metadata["error_kind"] == "connection_error"
    assert event.metadata["error_domain"] == "database"


def test_loki_connection_error_without_domain() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 5, tzinfo=UTC),
                    message="ERROR connection refused",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    log_events = [event for event in events if event.source == TimelineEventSource.LOKI]
    assert len(log_events) == 1

    event = log_events[0]
    assert event.metadata["error_kind"] == "connection_error"
    assert "error_domain" not in event.metadata


def test_loki_timeout_is_classified() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 5, tzinfo=UTC),
                    message="request timed out after 30s",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1

    event = events[0]
    assert event.metadata["error_kind"] == "timeout"


def test_loki_http_5xx_is_classified() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 5, tzinfo=UTC),
                    message="request failed with HTTP 503",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1

    event = events[0]
    assert event.metadata["error_kind"] == "http_5xx"


def test_loki_exception_is_classified() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 5, tzinfo=UTC),
                    message="RuntimeException: invalid configuration",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1

    event = events[0]
    assert event.metadata["error_kind"] == "exception"


def test_loki_normal_log_has_no_error_classification() -> None:
    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=datetime(2026, 8, 31, 10, 5, tzinfo=UTC),
                    message="INFO request completed successfully",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    log_events = [event for event in events if event.source == TimelineEventSource.LOKI]
    assert len(log_events) == 1

    event = log_events[0]
    assert event.severity == Severity.INFO
    assert event.title == "Application log"
    assert event.description == "INFO request completed successfully"
    assert "error_kind" not in event.metadata
    assert "error_domain" not in event.metadata


def test_build_ignores_kubernetes_event_without_timestamp() -> None:
    incident = _incident(
        events=[
            Event(
                type="Warning",
                reason="BackOff",
                message="Back-off restarting failed container",
                last_timestamp=None,
            )
        ],
    )

    events = TimelineBuilder().build(incident)
    assert events == []


def test_build_ignores_missing_loki_logs() -> None:
    incident = _incident()
    events = TimelineBuilder().build(incident)

    assert events == []


def test_build_sorts_events_chronologically() -> None:
    kubernetes_timestamp = datetime(2026, 8, 31, 10, 10, tzinfo=UTC)
    container_timestamp = datetime(2026, 8, 31, 10, 5, tzinfo=UTC)
    log_timestamp = datetime(2026, 8, 31, 10, 8, tzinfo=UTC)

    incident = _incident(
        events=[
            Event(
                type="Warning",
                reason="BackOff",
                message="Back-off restarting failed container",
                last_timestamp=kubernetes_timestamp,
            )
        ],
        containers=[
            ContainerSnapshot(
                name="api",
                started_at=container_timestamp,
                ready=True,
                image="image",
                restart_count=0,
            )
        ],
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=log_timestamp,
                    message="ERROR request failed",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 3
    assert [event.timestamp for event in events] == [
        container_timestamp,
        log_timestamp,
        kubernetes_timestamp,
    ]


def test_build_handles_multiple_loki_logs() -> None:
    first_timestamp = datetime(2026, 8, 31, 10, 1, tzinfo=UTC)
    second_timestamp = datetime(2026, 8, 31, 10, 2, tzinfo=UTC)
    third_timestamp = datetime(2026, 8, 31, 10, 3, tzinfo=UTC)

    incident = _incident(
        loki_logs=LogSnapshot(
            source=LogSource.LOKI.value,
            entries=[
                LogEntry(
                    timestamp=first_timestamp,
                    message="INFO request started",
                ),
                LogEntry(
                    timestamp=second_timestamp,
                    message="WARN request taking longer than expected",
                ),
                LogEntry(
                    timestamp=third_timestamp,
                    message="ERROR request failed",
                ),
            ],
        ),
    )

    events = TimelineBuilder().build(incident)

    assert len(events) == 3
    assert [event.severity for event in events] == [
        Severity.INFO,
        Severity.WARNING,
        Severity.ERROR,
    ]
    assert [event.title for event in events] == [
        "Application log",
        "Application warning",
        "Application error",
    ]


def test_build_preserves_metric_change_labels() -> None:
    timestamp = datetime(2026, 8, 31, 10, 3, tzinfo=UTC)

    labels = {
        "namespace": "default",
        "pod": "kubesage-api",
        "container": "api",
    }

    metric_change = MetricChange(
        metric_name="container_memory_usage",
        previous_value=100.0,
        value=200.0,
        timestamp=timestamp,
        labels=labels,
    )

    events = TimelineBuilder().build(
        _incident(),
        metric_changes=[metric_change],
    )

    assert events[0].metadata["labels"] == labels


def test_build_metric_change_decreased_value() -> None:
    timestamp = datetime(2026, 8, 31, 10, 3, tzinfo=UTC)

    metric_change = MetricChange(
        metric_name="container_cpu_usage",
        previous_value=0.8,
        value=0.2,
        timestamp=timestamp,
        labels={},
    )

    events = TimelineBuilder().build(
        _incident(),
        metric_changes=[metric_change],
    )

    assert events[0].title == "container_cpu_usage decreased"
    assert events[0].description == "container_cpu_usage decreased from 0.8 to 0.2."


def test_build_container_oomkilled_has_critical_severity() -> None:
    timestamp = datetime(2026, 8, 31, 10, 4, tzinfo=UTC)

    incident = _incident(
        containers=[
            ContainerSnapshot(
                name="api",
                finished_at=timestamp,
                last_exit_code=137,
                last_exit_reason="OOMKilled",
                ready=False,
                image="image",
                restart_count=0,
            )
        ],
    )

    events = TimelineBuilder().build(incident)

    assert len(events) == 1
    assert events[0].severity == Severity.CRITICAL


def test_build_container_crashloop_has_warning_severity() -> None:
    timestamp = datetime(2026, 8, 31, 10, 4, tzinfo=UTC)

    incident = _incident(
        containers=[
            ContainerSnapshot(
                name="api",
                finished_at=timestamp,
                last_exit_code=1,
                last_exit_reason="CrashLoopBackOff",
                ready=False,
                image="image",
                restart_count=0,
            )
        ],
    )

    events = TimelineBuilder().build(incident)

    assert len(events) == 1
    assert events[0].severity == Severity.WARNING


def test_build_container_backoff_has_warning_severity() -> None:
    timestamp = datetime(2026, 8, 31, 10, 4, tzinfo=UTC)

    incident = _incident(
        containers=[
            ContainerSnapshot(
                name="api",
                finished_at=timestamp,
                last_exit_code=1,
                last_exit_reason="BackOff",
                ready=False,
                image="image",
                restart_count=0,
            )
        ],
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1
    assert events[0].severity == Severity.WARNING


def test_build_kubernetes_normal_event_has_info_severity() -> None:
    timestamp = datetime(2026, 8, 31, 10, 6, tzinfo=UTC)

    incident = _incident(
        events=[
            Event(
                type="Normal",
                reason="Started",
                message="Started container api",
                last_timestamp=timestamp,
            )
        ],
    )

    events = TimelineBuilder().build(incident)
    assert len(events) == 1
    assert events[0].severity == Severity.INFO
