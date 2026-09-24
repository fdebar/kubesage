from datetime import UTC, datetime

from kubesage.watchers.incident_deduplicator import (
    IncidentDeduplicator,
)
from kubesage.watchers.models.incident_trigger import IncidentTrigger


def build_trigger(
    reason: str = "CrashLoopBackOff",
    pod_uid: str = "123e4567-e89b-12d3-a456-426614174000",
    resource_version: str = "12345",
) -> IncidentTrigger:
    return IncidentTrigger(
        namespace="production",
        pod="payment-api",
        pod_uid=pod_uid,
        resource_version=resource_version,
        reason=reason,
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
    second = build_trigger(reason="ImagePullBackOff")

    assert deduplicator.should_process(first) is True
    assert deduplicator.should_process(second) is True


def test_same_reason_with_new_resource_version_is_processed() -> None:
    deduplicator = IncidentDeduplicator()
    first = build_trigger(resource_version="100")
    second = build_trigger(resource_version="101")

    assert deduplicator.should_process(first) is True
    assert deduplicator.should_process(second) is True


def test_same_resource_version_is_deduplicated() -> None:
    deduplicator = IncidentDeduplicator()

    first = build_trigger(resource_version="100")
    second = build_trigger(resource_version="100")

    assert deduplicator.should_process(first) is True
    assert deduplicator.should_process(second) is False


def test_failed_trigger_can_be_reprocessed() -> None:
    deduplicator = IncidentDeduplicator()

    trigger = build_trigger(resource_version="100")
    assert deduplicator.should_process(trigger) is True

    deduplicator.forget(trigger)
    assert deduplicator.should_process(trigger) is True
