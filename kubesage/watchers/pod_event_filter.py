from datetime import UTC, datetime

from kubesage.models.analysis import AnalysisTrigger
from kubesage.watchers.models.incident_trigger import (
    IncidentTrigger,
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
        pod_uid: str,
    ) -> IncidentTrigger | None:
        if pod_state_diff.oom_killed:
            return self._trigger(
                namespace,
                pod,
                pod_uid,
                "OOMKilled",
                "Container killed because of memory limit",
            )

        reason = pod_state_diff.current_waiting_reason
        if (
            pod_state_diff.waiting_reason_changed
            and reason is not None
            and reason in INTERESTING_REASONS
        ):
            return self._trigger(
                namespace,
                pod,
                pod_uid,
                reason,
                f"Container entered {reason}",
            )

        return None

    def _trigger(
        self,
        namespace: str,
        pod: str,
        pod_uid: str,
        reason: str,
        message: str,
    ) -> IncidentTrigger:
        return IncidentTrigger(
            source=AnalysisTrigger.WATCHER,
            reason=reason,
            namespace=namespace,
            pod=pod,
            pod_uid=pod_uid,
            message=message,
            occurred_at=datetime.now(UTC),
        )
