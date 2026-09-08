from datetime import UTC, datetime, timedelta

from kubesage.builders.context.timeline_selector import TimelineSelector
from kubesage.models.finding import Severity
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)


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
