from datetime import UTC, datetime

from kubesage.models.finding import ResourceRef, Severity
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)


def test_timeline_event_creation() -> None:
    timestamp = datetime(2026, 8, 30, 12, 32, 24, tzinfo=UTC)

    event = TimelineEvent(
        id="event-123",
        timestamp=timestamp,
        type=TimelineEventType.POD_RESTART,
        source=TimelineEventSource.KUBERNETES,
        title="Pod restarted",
    )

    assert event.id == "event-123"
    assert event.timestamp == timestamp
    assert event.type == TimelineEventType.POD_RESTART
    assert event.source == TimelineEventSource.KUBERNETES
    assert event.title == "Pod restarted"
    assert event.description is None
    assert event.severity == Severity.INFO
    assert event.resource is None
    assert event.metadata == {}


def test_timeline_event_with_all_fields() -> None:
    timestamp = datetime(2026, 8, 30, 12, 32, 24, tzinfo=UTC)

    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="production",
        name="checkout-api-123",
    )

    event = TimelineEvent(
        id="event-456",
        timestamp=timestamp,
        type=TimelineEventType.METRIC_ANOMALY,
        source=TimelineEventSource.PROMETHEUS,
        title="Memory usage exceeded threshold",
        description="Container memory usage exceeded 90%.",
        severity=Severity.HIGH,
        resource=resource,
        metadata={
            "metric": "container_memory_working_set_bytes",
            "value": 8589934592,
            "threshold": 6442450944,
        },
    )

    assert event.description == "Container memory usage exceeded 90%."
    assert event.severity == Severity.HIGH
    assert event.resource == resource
    assert event.metadata["metric"] == "container_memory_working_set_bytes"
    assert event.metadata["value"] == 8589934592


def test_timeline_event_defaults_are_independent() -> None:
    first = TimelineEvent(
        id="event-1",
        timestamp=datetime.now(UTC),
        type=TimelineEventType.LOG_EVENT,
        source=TimelineEventSource.LOKI,
        title="Error log",
    )

    second = TimelineEvent(
        id="event-2",
        timestamp=datetime.now(UTC),
        type=TimelineEventType.LOG_EVENT,
        source=TimelineEventSource.LOKI,
        title="Another error log",
    )

    first.metadata["level"] = "ERROR"

    assert first.metadata == {"level": "ERROR"}
    assert second.metadata == {}


def test_timeline_event_serialization() -> None:
    timestamp = datetime(2026, 8, 30, 12, 32, 24, tzinfo=UTC)

    event = TimelineEvent(
        id="event-123",
        timestamp=timestamp,
        type=TimelineEventType.TRACE_EVENT,
        source=TimelineEventSource.TEMPO,
        title="Trace latency increased",
        severity=Severity.WARNING,
        metadata={
            "trace_id": "abc123",
            "duration_ms": 1842,
        },
    )

    data = event.model_dump(mode="json")

    assert data["id"] == "event-123"
    assert data["timestamp"] == "2026-08-30T12:32:24Z"
    assert data["type"] == "trace_event"
    assert data["source"] == "tempo"
    assert data["severity"] == "WARNING"
    assert data["metadata"]["trace_id"] == "abc123"


def test_timeline_event_with_resource_serializes_correctly() -> None:
    event = TimelineEvent(
        id="event-123",
        timestamp=datetime.now(UTC),
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="Container killed",
        resource=ResourceRef(
            api_version="v1",
            kind="Pod",
            namespace="default",
            name="api-123",
        ),
    )

    data = event.model_dump(mode="json")

    assert data["resource"] == {
        "api_version": "v1",
        "kind": "Pod",
        "namespace": "default",
        "name": "api-123",
    }
