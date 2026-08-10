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
        self,
        pod_state_diff: PodStateDiff,
        namespace: str,
        pod: str,
    ) -> IncidentTrigger | None:
        if pod_state_diff.oom_killed:
            return self._trigger(
                namespace,
                pod,
                "OOMKilled",
                "Container killed because of memory limit",
            )

        if pod_state_diff.phase_changed and pod_state_diff.current_phase == "Failed":
            return self._trigger(
                namespace,
                pod,
                "PodFailed",
                "Pod entered Failed phase",
            )

        if pod_state_diff.restart_delta > 0:
            return self._trigger(
                namespace,
                pod,
                "FrequentRestarts",
                f"Pod restarted {pod_state_diff.restart_delta} "
                f"time{'s' if pod_state_diff.restart_delta != 1 else ''}",
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

    def _trigger(
        self,
        namespace: str,
        pod: str,
        reason: str,
        message: str,
    ) -> IncidentTrigger:
        return IncidentTrigger(
            source="watcher",
            reason=reason,
            namespace=namespace,
            pod=pod,
            message=message,
            occurred_at=datetime.now(UTC),
        )
