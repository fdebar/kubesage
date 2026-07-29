from datetime import UTC, datetime

from kubesage.models.event import Event


def test_event() -> None:
    event = Event(
        type="Warning",
        reason="BackOff",
        message="Back-off restarting failed container",
        last_timestamp=datetime.fromisoformat("2023-01-01T00:00:00Z"),
    )

    assert event.type == "Warning"
    assert event.reason == "BackOff"
    assert event.message == "Back-off restarting failed container"
    assert event.last_timestamp == datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC)


def test_event_without_last_timestamp() -> None:
    event = Event(
        type="Warning",
        reason="BackOff",
        message="Back-off restarting failed container",
        last_timestamp=None,
    )

    assert event.last_timestamp is None
