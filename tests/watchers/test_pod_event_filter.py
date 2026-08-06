from datetime import UTC, datetime

from kubernetes.client import (
    V1ContainerState,
    V1ContainerStateWaiting,
    V1ContainerStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodStatus,
)

from kubesage.watchers.models.incident_trigger import PodWatchEvent
from kubesage.watchers.pod_event_filter import PodEventFilter


def build_pod(reason: str | None = None) -> V1Pod:
    waiting = None
    if reason:
        waiting = V1ContainerStateWaiting(
            reason=reason,
            message=f"Container waiting: {reason}",
        )

    return V1Pod(
        metadata=V1ObjectMeta(
            name="payment-api",
            namespace="production",
        ),
        status=V1PodStatus(
            container_statuses=[
                V1ContainerStatus(
                    name="payment",
                    image="payment:v1",
                    state=V1ContainerState(
                        waiting=waiting,
                    ),
                    image_id="image_id",
                    ready=True,
                    restart_count=0,
                )
            ]
        ),
    )


def build_event(pod: V1Pod, event_type: str = "MODIFIED") -> PodWatchEvent:
    return PodWatchEvent(type=event_type, pod=pod, received_at=datetime.now(UTC))


def test_build_trigger_returns_trigger_for_crash_loop() -> None:
    event_filter = PodEventFilter()
    event = build_event(build_pod("CrashLoopBackOff"))
    trigger = event_filter.build_trigger(event)

    assert trigger is not None
    assert trigger.reason == "CrashLoopBackOff"
    assert trigger.namespace == "production"
    assert trigger.pod == "payment-api"


def test_build_trigger_returns_none_for_non_incident_reason() -> None:
    event_filter = PodEventFilter()
    event = build_event(build_pod("ContainerCreating"))
    trigger = event_filter.build_trigger(event)

    assert trigger is None


def test_build_trigger_ignores_added_events() -> None:
    event_filter = PodEventFilter()
    event = build_event(build_pod("CrashLoopBackOff"), event_type="ADDED")
    trigger = event_filter.build_trigger(event)

    assert trigger is None


def test_build_trigger_ignores_pod_without_status() -> None:
    event_filter = PodEventFilter()
    pod = V1Pod(
        metadata=V1ObjectMeta(
            name="payment-api",
            namespace="production",
        )
    )
    event = build_event(pod)
    trigger = event_filter.build_trigger(event)

    assert trigger is None
