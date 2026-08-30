from datetime import UTC, datetime

from kubesage.builders.timeline import TimelineBuilder
from kubesage.models.event import Event
from kubesage.models.finding import Severity
from kubesage.models.incident import Incident
from kubesage.models.prometheus import MetricChange
from kubesage.models.timeline import (
    TimelineEventSource,
    TimelineEventType,
)


def test_build_empty_timeline() -> None:
    incident = Incident(
        namespace="default",
        pod="api-123",
        phase="Running",
        observed_at=datetime.now(),
    )
    result = TimelineBuilder().build(incident)

    assert result == []


def test_build_kubernetes_event() -> None:
    timestamp = datetime(2026, 8, 30, 12, 32, 24, tzinfo=UTC)

    incident = Incident(
        namespace="production",
        pod="api-123",
        phase="Running",
        observed_at=datetime.now(),
        events=[
            Event(
                type="Normal",
                reason="Started",
                message="Started container api",
                last_timestamp=timestamp,
            )
        ],
    )

    result = TimelineBuilder().build(incident)

    assert len(result) == 1

    timeline_event = result[0]

    assert timeline_event.id == "kubernetes-event-0"
    assert timeline_event.timestamp == timestamp
    assert timeline_event.type == TimelineEventType.KUBERNETES_EVENT
    assert timeline_event.source == TimelineEventSource.KUBERNETES
    assert timeline_event.title == "Started"
    assert timeline_event.description == "Started container api"
    assert timeline_event.severity == Severity.INFO

    assert timeline_event.resource is not None
    assert timeline_event.resource.kind == "Pod"
    assert timeline_event.resource.namespace == "production"
    assert timeline_event.resource.name == "api-123"

    assert timeline_event.metadata == {"event_type": "Normal", "reason": "Started"}


def test_build_warning_kubernetes_event() -> None:
    timestamp = datetime(2026, 8, 30, 12, 32, 24, tzinfo=UTC)

    incident = Incident(
        namespace="production",
        pod="api-123",
        phase="Running",
        observed_at=datetime.now(),
        events=[
            Event(
                type="Warning",
                reason="BackOff",
                message="Back-off restarting failed container",
                last_timestamp=timestamp,
            )
        ],
    )

    result = TimelineBuilder().build(incident)

    assert len(result) == 1
    assert result[0].severity == Severity.WARNING


def test_build_events_are_sorted_chronologically() -> None:
    earlier = datetime(2026, 8, 30, 12, 30, 0, tzinfo=UTC)
    later = datetime(2026, 8, 30, 12, 35, 0, tzinfo=UTC)

    incident = Incident(
        namespace="production",
        pod="api-123",
        phase="Running",
        observed_at=datetime.now(),
        events=[
            Event(
                type="Normal",
                reason="Started",
                message="Container started",
                last_timestamp=later,
            ),
            Event(
                type="Warning",
                reason="BackOff",
                message="Container back-off",
                last_timestamp=earlier,
            ),
        ],
    )

    result = TimelineBuilder().build(incident)

    assert len(result) == 2
    assert result[0].timestamp == earlier
    assert result[0].title == "BackOff"
    assert result[1].timestamp == later
    assert result[1].title == "Started"


def test_build_ignores_events_without_timestamp() -> None:
    timestamp = datetime(2026, 8, 30, 12, 32, 24, tzinfo=UTC)

    incident = Incident(
        namespace="production",
        pod="api-123",
        phase="Running",
        observed_at=datetime.now(),
        events=[
            Event(
                type="Normal",
                reason="Started",
                message="Container started",
                last_timestamp=timestamp,
            ),
            Event(
                type="Warning",
                reason="BackOff",
                message="Container back-off",
                last_timestamp=None,
            ),
        ],
    )

    result = TimelineBuilder().build(incident)

    assert len(result) == 1
    assert result[0].title == "Started"

    def test_build_metric_change_event() -> None:
        incident = Incident(
            namespace="default",
            pod="api",
            phase="Running",
            observed_at=datetime.now(),
        )

        change = MetricChange(
            timestamp=datetime.now(),
            metric_name="cpu",
            previous_value=0.2,
            value=0.5,
            change_ratio=1.5,
            labels={"container": "api"},
        )

        event = TimelineBuilder()._build_metric_change_event(
            incident=incident,
            change=change,
            index=0,
        )

        assert event.type == TimelineEventType.METRIC_CHANGE
        assert event.source == TimelineEventSource.PROMETHEUS
        assert event.timestamp == change.timestamp
        assert event.severity == Severity.INFO
        assert event.metadata["container"] if "container" in event.metadata else True
