from datetime import UTC, datetime, timedelta

from _pytest.monkeypatch import MonkeyPatch

from kubesage.builders.context.timeline_selector import TimelineSelector
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)


def make_event(
    event_id: str,
    *,
    offset_seconds: int = 0,
    event_type: TimelineEventType = TimelineEventType.LOG_EVENT,
    severity: Severity = Severity.INFO,
    title: str = "Log message",
    description: str | None = None,
    metadata: dict | None = None,
) -> TimelineEvent:
    timestamp = datetime(2026, 9, 4, 10, 0, 0, tzinfo=UTC) + timedelta(
        seconds=offset_seconds
    )

    return TimelineEvent(
        id=event_id,
        timestamp=timestamp,
        type=event_type,
        source=TimelineEventSource.LOKI,
        title=title,
        description=description,
        severity=severity,
        metadata=metadata or {},
    )


def make_finding(
    title: str = "Database connection failure",
    rule: str = "application_error",
) -> Finding:
    return Finding(
        rule=rule,
        title=title,
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.ERROR,
        confidence=0.9,
        description="Application database connection failed.",
    )


def test_empty_timeline_returns_empty_list() -> None:
    selector = TimelineSelector()

    result = selector.select([], [])
    assert result == []


def test_error_event_is_retained() -> None:
    selector = TimelineSelector()

    event = make_event(
        "error-1",
        severity=Severity.ERROR,
        title="Database connection failed",
    )

    result = selector.select([event], [])

    assert [event.id for event in result] == ["error-1"]


def test_warning_event_is_retained() -> None:
    selector = TimelineSelector()

    event = make_event(
        "warning-1",
        severity=Severity.WARNING,
        title="High memory usage",
    )

    result = selector.select([event], [])

    assert [event.id for event in result] == ["warning-1"]


def test_banal_info_event_is_not_retained() -> None:
    selector = TimelineSelector()

    event = make_event("info-1", title="Routine application log")
    result = selector.select([event], [])

    assert result == []


def test_pod_restart_is_retained() -> None:
    selector = TimelineSelector()

    event = make_event(
        "restart-1",
        event_type=TimelineEventType.POD_RESTART,
        title="Pod restarted",
    )

    result = selector.select([event], [])

    assert [event.id for event in result] == ["restart-1"]


def test_container_termination_is_retained() -> None:
    selector = TimelineSelector()

    event = make_event(
        "terminated-1",
        event_type=TimelineEventType.CONTAINER_TERMINATED,
        title="Container terminated",
    )

    result = selector.select([event], [])

    assert [event.id for event in result] == ["terminated-1"]


def test_classified_application_error_is_retained() -> None:
    selector = TimelineSelector()

    event = make_event(
        "app-error-1",
        title="Application error",
        metadata={
            "error_kind": "connection_failure",
            "error_domain": "database",
        },
    )

    result = selector.select([event], [])

    assert [event.id for event in result] == ["app-error-1"]


def test_event_near_important_event_is_retained() -> None:
    selector = TimelineSelector()

    important = make_event(
        "error-1",
        offset_seconds=100,
        severity=Severity.ERROR,
        title="Database failure",
    )

    nearby = make_event(
        "nearby-1",
        offset_seconds=80,
        title="Connection attempt",
    )

    unrelated = make_event(
        "unrelated-1",
        offset_seconds=200,
        title="Routine log",
    )

    result = selector.select(
        [important, nearby, unrelated],
        [],
    )

    result_ids = {event.id for event in result}

    assert "error-1" in result_ids
    assert "nearby-1" in result_ids
    assert "unrelated-1" not in result_ids


def test_event_related_to_finding_is_retained() -> None:
    selector = TimelineSelector()

    event = make_event("database-1", title="Database connection failure")

    finding = make_finding()

    result = selector.select([event], [finding])

    assert [event.id for event in result] == ["database-1"]


def test_repeated_info_events_are_deduplicated() -> None:
    selector = TimelineSelector()

    events = [
        make_event("info-1", title="Routine log"),
        make_event("info-2", title="Routine log"),
        make_event("info-3", title="Routine log"),
    ]

    result = selector.select(events, [])

    assert len(result) == 0


def test_repeated_important_events_are_not_deduplicated() -> None:
    selector = TimelineSelector()

    events = [
        make_event(
            "error-1",
            severity=Severity.ERROR,
            title="Database failure",
        ),
        make_event(
            "error-2",
            severity=Severity.ERROR,
            title="Database failure",
        ),
    ]

    result = selector.select(events, [])

    assert len(result) == 2


def test_timeline_is_limited_to_max_events(monkeypatch: MonkeyPatch) -> None:
    selector = TimelineSelector()

    monkeypatch.setattr(
        "kubesage.builders.context.timeline_selector.settings.ai_timeline_max_events",
        5,
    )

    events = [
        make_event(
            f"error-{index}",
            offset_seconds=index,
            severity=Severity.ERROR,
            title=f"Error {index}",
        )
        for index in range(10)
    ]

    result = selector.select(events, [])

    assert len(result) == 5


def test_important_events_are_prioritized_when_limit_is_reached(
    monkeypatch: MonkeyPatch,
) -> None:
    selector = TimelineSelector()

    monkeypatch.setattr(
        "kubesage.builders.context.timeline_selector.settings.ai_timeline_max_events",
        2,
    )

    events = [
        make_event("info-1", offset_seconds=1, title="Routine log"),
        make_event("info-2", offset_seconds=2, title="Routine log 2"),
        make_event(
            "error-1",
            offset_seconds=3,
            severity=Severity.ERROR,
            title="Critical database failure",
        ),
    ]

    result = selector.select(events, [])

    result_ids = {event.id for event in result}

    assert "error-1" in result_ids
    assert len(result) == 2
