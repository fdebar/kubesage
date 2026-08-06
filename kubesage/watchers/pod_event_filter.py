from datetime import UTC, datetime

from kubesage.watchers.models.incident_trigger import (
    IncidentTrigger,
    PodWatchEvent,
)
from kubesage.watchers.models.pod_state_diff import PodStateDiff

INTERESTING_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerConfigError",
    "RunContainerError",
}


class PodEventFilter:
    """
    Determines whether a Kubernetes pod event
    should trigger an analysis.
    """

    def evaluate(
        self, diff: PodStateDiff, namespace: str, pod: str
    ) -> IncidentTrigger | None:
        if diff.restart_delta >= 3:
            return IncidentTrigger(
                namespace=namespace,
                pod=pod,
                reason="FrequentRestarts",
                message=(f"Pod restarted {diff.restart_delta} times"),
                occurred_at=datetime.now(UTC),
            )

        return None

    def build_trigger(self, event: PodWatchEvent) -> IncidentTrigger | None:
        if event.type != "MODIFIED":
            return None

        pod = event.pod
        if pod.status is None:
            return None

        statuses = pod.status.container_statuses or []
        for container in statuses:
            state = container.state
            if state is None or state.waiting is None:
                continue

            reason = state.waiting.reason
            if reason not in INTERESTING_REASONS:
                continue

            return IncidentTrigger(
                source="kubernetes",
                reason=reason,
                namespace=pod.metadata.namespace,
                pod=pod.metadata.name,
                message=state.waiting.message,
                occurred_at=event.received_at,
            )

        return None
