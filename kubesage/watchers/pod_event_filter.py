from datetime import UTC, datetime

from kubernetes.client import V1Pod

from kubesage.models.analysis import AnalysisTrigger
from kubesage.watchers.models.incident_trigger import IncidentTrigger
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
    Determines whether a Pod state change should trigger an analysis.
    """

    def evaluate(
        self,
        pod_state_diff: PodStateDiff,
        namespace: str,
        pod: str,
        pod_uid: str,
        resource_version: str,
    ) -> IncidentTrigger | None:

        if pod_state_diff.oom_killed:
            return self._trigger(
                namespace=namespace,
                pod=pod,
                pod_uid=pod_uid,
                resource_version=resource_version,
                reason="OOMKilled",
                message="Container killed because of memory limit",
            )

        reason = pod_state_diff.current_waiting_reason
        if (
            pod_state_diff.waiting_reason_changed
            and reason is not None
            and reason in INTERESTING_REASONS
        ):
            return self._trigger(
                namespace=namespace,
                pod=pod,
                pod_uid=pod_uid,
                resource_version=resource_version,
                reason=reason,
                message=f"Container entered {reason}",
            )

        return None

    def evaluate_current(self, pod: V1Pod) -> IncidentTrigger | None:
        """Return an incident trigger for a problematic current Pod state."""
        metadata = pod.metadata
        if (
            metadata is None
            or metadata.namespace is None
            or metadata.name is None
            or metadata.uid is None
            or metadata.resource_version is None
        ):
            return None

        namespace = metadata.namespace
        name = metadata.name
        uid = metadata.uid
        resource_version = metadata.resource_version

        issue = self.current_issue(pod)
        if issue is not None:
            reason, message = issue
            return self._trigger(
                namespace=namespace,
                pod=name,
                pod_uid=uid,
                resource_version=resource_version,
                reason=reason,
                message=message,
            )

        return None

    def current_issue(self, pod: V1Pod) -> tuple[str, str] | None:
        """Return the currently active watcher condition, if any."""
        reason = self._waiting_reason(pod)
        if reason in INTERESTING_REASONS:
            return reason, f"Container is in {reason}"

        if self._is_oom_killed(pod):
            return "OOMKilled", "Container killed because of memory limit"

        return None

    @staticmethod
    def _waiting_reason(pod: V1Pod) -> str | None:
        if pod.status is None or pod.status.container_statuses is None:
            return None

        for container in pod.status.container_statuses:
            state = container.state
            if state is not None and state.waiting is not None and state.waiting.reason:
                return str(state.waiting.reason)

        return None

    @staticmethod
    def _is_oom_killed(pod: V1Pod) -> bool:
        if pod.status is None or pod.status.container_statuses is None:
            return False

        containers = pod.status.container_statuses
        if containers and all(container.ready for container in containers):
            return False

        return any(
            container.last_state is not None
            and container.last_state.terminated is not None
            and container.last_state.terminated.reason == "OOMKilled"
            for container in containers
        )

    def _trigger(
        self,
        namespace: str,
        pod: str,
        pod_uid: str,
        resource_version: str,
        reason: str,
        message: str,
    ) -> IncidentTrigger:
        return IncidentTrigger(
            source=AnalysisTrigger.WATCHER,
            reason=reason,
            namespace=namespace,
            pod=pod,
            pod_uid=pod_uid,
            resource_version=resource_version,
            message=message,
            occurred_at=datetime.now(UTC),
        )
