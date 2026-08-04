from datetime import UTC, datetime

from kubesage.watchers.incident_deduplicator import (
    IncidentDeduplicator,
)
from kubesage.watchers.models import IncidentTrigger


def build_trigger() -> IncidentTrigger:
    return IncidentTrigger(
        namespace="production",
        pod="payment-api",
        reason="CrashLoopBackOff",
        message="container crashed",
        occurred_at=datetime.now(UTC),
    )


def test_first_incident_is_processed() -> None:
    deduplicator = IncidentDeduplicator()
    trigger = build_trigger()

    assert deduplicator.should_process(trigger) is True


def test_duplicate_incident_is_ignored() -> None:
    deduplicator = IncidentDeduplicator()
    trigger = build_trigger()

    assert deduplicator.should_process(trigger) is True
    assert deduplicator.should_process(trigger) is False


def test_different_reason_is_processed() -> None:
    deduplicator = IncidentDeduplicator()
    first = build_trigger()
    second = IncidentTrigger(
        namespace="production",
        pod="payment-api",
        reason="ImagePullBackOff",
        occurred_at=datetime.now(UTC),
    )

    assert deduplicator.should_process(first) is True
    assert deduplicator.should_process(second) is True
