from datetime import UTC, datetime, timedelta

from _pytest.monkeypatch import MonkeyPatch

from kubesage.builders.context.timeline_selector import TimelineSelector
from kubesage.models.finding import Finding, ResourceRef, Severity
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)
from kubesage.utils.config import settings


def _log_event(
    event_id: str,
    timestamp: datetime,
    message: str,
    error_kind: str | None = None,
    container: str = "grafana",
) -> TimelineEvent:
    metadata: dict[str, object] = {
        "labels": {
            "container": container,
        }
    }

    if error_kind:
        metadata["error_kind"] = error_kind

    return TimelineEvent(
        id=event_id,
        timestamp=timestamp,
        type=TimelineEventType.LOG_EVENT,
        source=TimelineEventSource.LOKI,
        title="Application log",
        description=message,
        severity=Severity.INFO,
        metadata=metadata,
    )


def test_select_keeps_single_application_error() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    selected = selector.select(
        [
            _log_event(
                "error-1",
                timestamp,
                "Failed resource call to Tempo",
                error_kind="timeout",
            )
        ],
        [],
    )

    assert len(selected) == 1
    assert selected[0].id == "error-1"


def test_select_aggregates_repeated_application_errors() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    timeline = [
        _log_event(
            "error-1",
            timestamp,
            "Failed resource call to Tempo",
            error_kind="timeout",
        ),
        _log_event(
            "error-2",
            timestamp + timedelta(seconds=5),
            "Failed resource call to Tempo",
            error_kind="timeout",
        ),
        _log_event(
            "error-3",
            timestamp + timedelta(seconds=10),
            "Failed resource call to Tempo",
            error_kind="timeout",
        ),
    ]

    selected = selector.select(timeline, [])

    aggregated = [event for event in selected if event.metadata.get("aggregated")]
    assert len(aggregated) == 1

    aggregate = aggregated[0]
    assert aggregate.metadata["occurrences"] == 3
    assert aggregate.metadata["error_kinds"] == {"timeout": 3}
    assert aggregate.metadata["first_seen"] == (timestamp.isoformat())
    assert aggregate.metadata["last_seen"] == (
        (timestamp + timedelta(seconds=10)).isoformat()
    )


def test_select_aggregates_different_error_kinds_in_same_episode() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    timeline = [
        _log_event(
            "error-1",
            timestamp,
            "Failed resource call to Tempo",
            error_kind="timeout",
        ),
        _log_event(
            "error-2",
            timestamp + timedelta(seconds=2),
            "Failed to send request to Tempo",
            error_kind="connection_error",
        ),
        _log_event(
            "error-3",
            timestamp + timedelta(seconds=4),
            "Error processing TraceQL query",
            error_kind="generic_error",
        ),
    ]

    selected = selector.select(timeline, [])

    aggregated = [event for event in selected if event.metadata.get("aggregated")]
    assert len(aggregated) == 1
    assert aggregated[0].metadata["occurrences"] == 3
    assert aggregated[0].metadata["error_kinds"] == {
        "timeout": 1,
        "connection_error": 1,
        "generic_error": 1,
    }


def test_select_keeps_separated_error_episodes() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    timeline = [
        _log_event(
            "error-1",
            timestamp,
            "Tempo request failed",
            error_kind="timeout",
        ),
        _log_event(
            "error-2",
            timestamp + timedelta(seconds=5),
            "Tempo request failed",
            error_kind="timeout",
        ),
        _log_event(
            "error-3",
            timestamp + timedelta(seconds=40),
            "Tempo request failed",
            error_kind="timeout",
        ),
    ]

    selected = selector.select(timeline, [])

    aggregated = [event for event in selected if event.metadata.get("aggregated")]
    assert len(aggregated) == 1
    assert aggregated[0].metadata["occurrences"] == 2

    selected_ids = {event.id for event in selected}
    assert "error-3" in selected_ids


def test_select_does_not_select_normal_info_logs() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    timeline = [
        _log_event(
            "info-1",
            timestamp,
            "Loading incluster config...",
        ),
        _log_event(
            "info-2",
            timestamp + timedelta(seconds=1),
            "Loading incluster config...",
        ),
    ]

    selected = selector.select(timeline, [])
    assert selected == []


def test_select_keeps_kubernetes_events_individual() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    event = TimelineEvent(
        id="unhealthy-1",
        timestamp=timestamp,
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="Unhealthy",
        description="Readiness probe failed",
        severity=Severity.WARNING,
    )

    selected = selector.select([event], [])

    assert len(selected) == 1
    assert selected[0].id == "unhealthy-1"
    assert selected[0].metadata.get("aggregated") is not True


def test_select_keeps_container_started_individual() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    event = TimelineEvent(
        id="started-1",
        timestamp=timestamp,
        type=TimelineEventType.CONTAINER_STARTED,
        source=TimelineEventSource.KUBERNETES,
        title="Container started",
        severity=Severity.INFO,
    )

    selected = selector.select([event], [])
    assert len(selected) == 1
    assert selected[0].id == "started-1"


def test_select_does_not_return_raw_events_replaced_by_aggregate() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    timeline = [
        _log_event(
            "error-1",
            timestamp,
            "Failed resource call to Tempo",
            error_kind="timeout",
        ),
        _log_event(
            "error-2",
            timestamp + timedelta(seconds=2),
            "Failed to send request to Tempo",
            error_kind="connection_error",
        ),
        _log_event(
            "error-3",
            timestamp + timedelta(seconds=4),
            "Error processing TraceQL query",
            error_kind="generic_error",
        ),
    ]

    selected = selector.select(timeline, [])
    selected_ids = {event.id for event in selected}

    assert "error-1" not in selected_ids
    assert "error-2" not in selected_ids
    assert "error-3" not in selected_ids

    aggregated = [event for event in selected if event.metadata.get("aggregated")]
    assert len(aggregated) == 1


def test_select_keeps_context_around_aggregated_error() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    started = TimelineEvent(
        id="started",
        timestamp=timestamp,
        type=TimelineEventType.CONTAINER_STARTED,
        source=TimelineEventSource.KUBERNETES,
        title="Container started",
        severity=Severity.INFO,
    )

    error_1 = _log_event(
        "error-1",
        timestamp + timedelta(seconds=5),
        "Tempo timeout",
        error_kind="timeout",
    )

    error_2 = _log_event(
        "error-2",
        timestamp + timedelta(seconds=7),
        "Tempo connection refused",
        error_kind="connection_error",
    )

    selected = selector.select([started, error_1, error_2], [])
    selected_ids = {event.id for event in selected}
    assert "started" in selected_ids

    aggregated = [event for event in selected if event.metadata.get("aggregated")]
    assert len(aggregated) == 1
    assert aggregated[0].metadata["occurrences"] == 2


def test_select_grafana_error_episode_is_compact() -> None:
    selector = TimelineSelector()
    timestamp = datetime.now(UTC)

    timeline = [
        TimelineEvent(
            id="started",
            timestamp=timestamp,
            type=TimelineEventType.CONTAINER_STARTED,
            source=TimelineEventSource.KUBERNETES,
            title="Container started",
            severity=Severity.INFO,
        ),
        _log_event(
            "loading-1",
            timestamp + timedelta(seconds=1),
            "Loading incluster config...",
        ),
        _log_event(
            "loading-2",
            timestamp + timedelta(seconds=1),
            "Loading incluster config...",
        ),
        _log_event(
            "error-1",
            timestamp + timedelta(seconds=10),
            "Failed resource call to Tempo: timeout awaiting response headers",
            error_kind="timeout",
        ),
        _log_event(
            "error-2",
            timestamp + timedelta(seconds=12),
            "Failed to send request to Tempo: connection refused",
            error_kind="connection_error",
        ),
        _log_event(
            "error-3",
            timestamp + timedelta(seconds=14),
            "Error processing TraceQL query",
            error_kind="generic_error",
        ),
        TimelineEvent(
            id="unhealthy",
            timestamp=timestamp + timedelta(seconds=16),
            type=TimelineEventType.KUBERNETES_EVENT,
            source=TimelineEventSource.KUBERNETES,
            title="Unhealthy",
            severity=Severity.WARNING,
        ),
    ]

    selected = selector.select(timeline, [])
    selected_ids = {event.id for event in selected}

    assert "started" in selected_ids
    assert "unhealthy" in selected_ids

    assert "loading-1" not in selected_ids
    assert "loading-2" not in selected_ids

    aggregates = [event for event in selected if event.metadata.get("aggregated")]
    assert len(aggregates) == 1

    aggregate = aggregates[0]
    assert aggregate.metadata["occurrences"] == 3
    assert aggregate.metadata["error_kinds"] == {
        "timeout": 1,
        "connection_error": 1,
        "generic_error": 1,
    }
    assert len(selected) == 3


def test_select_keeps_event_related_to_finding_title() -> None:
    event = _log_event("event-1", datetime.now(UTC), "Database connection failure")
    finding = Finding(
        title="Database connection failure",
        rule="DatabaseConnectionRule",
        severity=Severity.ERROR,
        description="Database connection is failing.",
    )

    selected = TimelineSelector().select([event], [finding])
    assert [event.id for event in selected] == ["event-1"]


def test_select_keeps_event_related_to_finding_rule() -> None:
    event = _log_event(
        "event-1",
        datetime(2026, 9, 8, 12, 0, 0),
        "Connection refused by database",
        error_kind="connection_refused",
    )

    finding = Finding(
        title="Database unavailable",
        rule="ConnectionRefusedRule",
        severity=Severity.ERROR,
        description="The database refused the connection.",
    )

    selected = TimelineSelector().select([event], [finding])
    assert [event.id for event in selected] == ["event-1"]


def test_select_does_not_keep_event_unrelated_to_findings() -> None:
    event = _log_event(
        "event-1",
        datetime(2026, 9, 8, 12, 0, 0),
        "User authentication succeeded",
    )
    finding = Finding(
        title="Database unavailable",
        rule="DatabaseConnectionRule",
        severity=Severity.ERROR,
        description="The database is unavailable.",
    )

    selected = TimelineSelector().select([event], [finding])
    assert selected == []


def test_select_does_not_double_count_error_related_to_finding() -> None:
    event = _log_event(
        "event-1",
        datetime.now(UTC),
        "Database connection timeout",
        error_kind="timeout",
    )

    finding = Finding(
        title="Database connection timeout",
        rule="DatabaseTimeoutRule",
        severity=Severity.ERROR,
        description="Database connection is timing out.",
    )

    selected = TimelineSelector().select([event], [finding])

    assert len(selected) == 1
    assert selected[0].id == "event-1"
    assert selected[0].metadata.get("aggregated") is not True


def test_select_aggregates_errors_at_exact_cluster_window_boundary() -> None:
    window = settings.ai_timeline_error_cluster_window_seconds
    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    events = [
        _log_event(
            "event-1",
            timestamp,
            "Database timeout",
            error_kind="timeout",
        ),
        _log_event(
            "event-2",
            timestamp + timedelta(seconds=window),
            "Database timeout",
            error_kind="timeout",
        ),
    ]

    selected = TimelineSelector().select(events, [])
    aggregated = [
        event for event in selected if event.metadata.get("aggregated") is True
    ]

    assert len(aggregated) == 1
    assert aggregated[0].metadata["occurrences"] == 2


def test_select_does_not_aggregate_errors_outside_cluster_window() -> None:
    window = settings.ai_timeline_error_cluster_window_seconds
    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    events = [
        _log_event(
            "event-1",
            timestamp,
            "Database timeout",
            error_kind="timeout",
        ),
        _log_event(
            "event-2",
            timestamp + timedelta(seconds=window + 1),
            "Database timeout",
            error_kind="timeout",
        ),
    ]
    selected = TimelineSelector().select(events, [])

    assert len(selected) == 2
    assert all(event.metadata.get("aggregated") is not True for event in selected)


def test_select_does_not_aggregate_errors_from_different_resources() -> None:
    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    event_a = _log_event(
        "event-a",
        timestamp,
        "Database timeout",
        error_kind="timeout",
    )
    event_a.resource = ResourceRef(
        namespace="default",
        kind="Pod",
        name="app-a",
    )
    event_b = _log_event(
        "event-b",
        timestamp + timedelta(seconds=1),
        "Database timeout",
        error_kind="timeout",
    )
    event_b.resource = ResourceRef(
        namespace="default",
        kind="Pod",
        name="app-b",
    )

    selected = TimelineSelector().select([event_a, event_b], [])

    assert len(selected) == 2
    assert all(event.metadata.get("aggregated") is not True for event in selected)


def test_select_aggregates_errors_from_same_resource() -> None:
    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    event_a = _log_event(
        "event-a",
        timestamp,
        "Database timeout",
        error_kind="timeout",
    )
    event_a.resource = ResourceRef(
        namespace="default",
        kind="Pod",
        name="app",
    )

    event_b = _log_event(
        "event-b",
        timestamp + timedelta(seconds=1),
        "Database connection refused",
        error_kind="connection_refused",
    )
    event_b.resource = ResourceRef(
        namespace="default",
        kind="Pod",
        name="app",
    )

    selected = TimelineSelector().select([event_a, event_b], [])

    aggregated = [
        event for event in selected if event.metadata.get("aggregated") is True
    ]

    assert len(aggregated) == 1
    assert aggregated[0].metadata["occurrences"] == 2


def test_select_keeps_event_at_context_window_boundaries() -> None:
    before = settings.ai_timeline_window_before_seconds
    after = settings.ai_timeline_window_after_seconds

    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    important = TimelineEvent(
        id="important",
        timestamp=timestamp,
        type=TimelineEventType.POD_RESTART,
        source=TimelineEventSource.KUBERNETES,
        title="Pod restarted",
        severity=Severity.WARNING,
    )

    before_event = TimelineEvent(
        id="before",
        timestamp=timestamp - timedelta(seconds=before),
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="Before event",
        severity=Severity.INFO,
    )

    after_event = TimelineEvent(
        id="after",
        timestamp=timestamp + timedelta(seconds=after),
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="After event",
        severity=Severity.INFO,
    )

    selected = TimelineSelector().select(
        [before_event, important, after_event],
        [],
    )

    selected_ids = {event.id for event in selected}

    assert "important" in selected_ids
    assert "before" in selected_ids
    assert "after" in selected_ids


def test_select_excludes_normal_info_logs_from_context() -> None:
    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    important = TimelineEvent(
        id="restart",
        timestamp=timestamp,
        type=TimelineEventType.POD_RESTART,
        source=TimelineEventSource.KUBERNETES,
        title="Pod restarted",
        severity=Severity.WARNING,
    )

    info_log = _log_event(
        "info-log",
        timestamp + timedelta(seconds=1),
        "HTTP request completed successfully",
    )

    selected = TimelineSelector().select([important, info_log], [])
    selected_ids = {event.id for event in selected}

    assert "restart" in selected_ids
    assert "info-log" not in selected_ids


def test_select_deduplicates_info_non_log_events() -> None:
    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    event_a = TimelineEvent(
        id="event-a",
        timestamp=timestamp,
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="Scheduled",
        severity=Severity.INFO,
    )

    event_b = TimelineEvent(
        id="event-b",
        timestamp=timestamp + timedelta(seconds=1),
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="Scheduled",
        severity=Severity.INFO,
    )

    selected = TimelineSelector().select([event_a, event_b], [])

    assert len(selected) == 1


def test_select_keeps_duplicate_non_info_events() -> None:
    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    event_a = TimelineEvent(
        id="event-a",
        timestamp=timestamp,
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="Failed",
        severity=Severity.ERROR,
    )

    event_b = TimelineEvent(
        id="event-b",
        timestamp=timestamp + timedelta(seconds=1),
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="Failed",
        severity=Severity.ERROR,
    )

    selected = TimelineSelector().select([event_a, event_b], [])

    assert len(selected) == 2


def test_select_does_not_deduplicate_log_events() -> None:
    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    event_a = _log_event(
        "event-a",
        timestamp,
        "Application error",
        error_kind="exception",
    )

    event_b = _log_event(
        "event-b",
        timestamp + timedelta(seconds=1),
        "Application error",
        error_kind="exception",
    )

    selected = TimelineSelector().select([event_a, event_b], [])
    aggregated = [
        event for event in selected if event.metadata.get("aggregated") is True
    ]

    assert len(aggregated) == 1
    assert aggregated[0].metadata["occurrences"] == 2


def test_select_respects_max_event_limit(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_timeline_max_events", 2)
    timestamp = datetime(2026, 9, 8, 12, 0, 0)
    events = [
        TimelineEvent(
            id=f"restart-{index}",
            timestamp=timestamp + timedelta(seconds=index),
            type=TimelineEventType.POD_RESTART,
            source=TimelineEventSource.KUBERNETES,
            title=f"Pod restarted {index}",
            severity=Severity.WARNING,
        )
        for index in range(5)
    ]
    selected = TimelineSelector().select(events, [])

    assert len(selected) == 2


def test_select_prioritizes_high_severity_events_when_limited(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_timeline_max_events", 1)
    timestamp = datetime(2026, 9, 8, 12, 0, 0)
    info_event = TimelineEvent(
        id="info",
        timestamp=timestamp,
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="Normal event",
        severity=Severity.INFO,
    )

    critical_event = TimelineEvent(
        id="critical",
        timestamp=timestamp + timedelta(seconds=1),
        type=TimelineEventType.LOG_EVENT,
        source=TimelineEventSource.LOKI,
        title="Critical error",
        severity=Severity.CRITICAL,
        metadata={"error_kind": "exception"},
    )

    selected = TimelineSelector().select([info_event, critical_event], [])

    assert [event.id for event in selected] == ["critical"]


def test_select_returns_selected_events_in_chronological_order(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_timeline_max_events", 3)

    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    events = [
        TimelineEvent(
            id="late",
            timestamp=timestamp + timedelta(minutes=3),
            type=TimelineEventType.POD_RESTART,
            source=TimelineEventSource.KUBERNETES,
            title="Late restart",
            severity=Severity.CRITICAL,
        ),
        TimelineEvent(
            id="early",
            timestamp=timestamp,
            type=TimelineEventType.POD_RESTART,
            source=TimelineEventSource.KUBERNETES,
            title="Early restart",
            severity=Severity.WARNING,
        ),
        TimelineEvent(
            id="middle",
            timestamp=timestamp + timedelta(minutes=1),
            type=TimelineEventType.POD_RESTART,
            source=TimelineEventSource.KUBERNETES,
            title="Middle restart",
            severity=Severity.ERROR,
        ),
    ]

    selected = TimelineSelector().select(events, [])

    assert [event.id for event in selected] == ["early", "middle", "late"]


def test_select_keeps_error_trace_event() -> None:
    timestamp = datetime(2026, 9, 8, 12, 0, 0)

    event = TimelineEvent(
        id="trace-error",
        timestamp=timestamp,
        type=TimelineEventType.TRACE_EVENT,
        source=TimelineEventSource.TEMPO,
        title="Trace error",
        severity=Severity.ERROR,
    )

    selected = TimelineSelector().select([event], [])

    assert [event.id for event in selected] == ["trace-error"]
