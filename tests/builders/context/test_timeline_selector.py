from datetime import datetime, timedelta

from kubesage.builders.context.timeline_selector import TimelineSelector
from kubesage.models.finding import Severity
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)


def make_event(
    event_id: str,
    timestamp: datetime,
    *,
    title: str,
    severity: Severity = Severity.INFO,
    event_type: TimelineEventType = TimelineEventType.LOG_EVENT,
    metadata: dict | None = None,
) -> TimelineEvent:
    return TimelineEvent(
        id=event_id,
        timestamp=timestamp,
        type=event_type,
        source=TimelineEventSource.LOKI,
        title=title,
        severity=severity,
        metadata=metadata or {},
    )


def test_error_event_is_selected() -> None:
    now = datetime.now()

    timeline = [
        make_event("1", now, title="connection refused", severity=Severity.ERROR)
    ]
    selected = TimelineSelector().select(timeline=timeline, findings=[], events=[])

    assert [event.id for event in selected] == ["1"]


def test_unimportant_info_event_is_not_selected() -> None:
    now = datetime.now()

    timeline = [make_event("1", now, title="routine request completed")]
    selected = TimelineSelector().select(timeline=timeline, findings=[], events=[])

    assert selected == []


def test_pod_restart_is_selected() -> None:
    now = datetime.now()

    timeline = [
        make_event(
            "1", now, title="Pod restarted", event_type=TimelineEventType.POD_RESTART
        )
    ]
    selected = TimelineSelector().select(timeline=timeline, findings=[], events=[])

    assert [event.id for event in selected] == ["1"]


def test_classified_application_error_is_selected() -> None:
    now = datetime.now()

    timeline = [
        make_event(
            "1",
            now,
            title="Application error",
            metadata={"error_kind": "connection_refused", "error_domain": "database"},
        ),
    ]

    selected = TimelineSelector().select(timeline=timeline, findings=[], events=[])

    assert [event.id for event in selected] == ["1"]


def test_context_around_important_event_is_selected() -> None:
    now = datetime.now()

    timeline = [
        make_event("before", now - timedelta(seconds=10), title="request started"),
        make_event("error", now, title="connection refused", severity=Severity.ERROR),
        make_event("after", now + timedelta(seconds=5), title="request aborted"),
        make_event("far", now + timedelta(minutes=5), title="unrelated request"),
    ]

    selected = TimelineSelector().select(timeline=timeline, findings=[], events=[])
    ids = {event.id for event in selected}

    assert "error" in ids
    assert "before" in ids
    assert "after" in ids
    assert "far" not in ids
