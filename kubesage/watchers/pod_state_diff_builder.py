from kubernetes.client import V1Pod

from kubesage.watchers.models.pod_state_diff import (
    PodStateDiff,
)


class PodStateDiffBuilder:
    """
    Responsible for building a diff between two states of a Pod.
    """

    def build(self, previous: V1Pod | None, current: V1Pod) -> PodStateDiff:
        previous_phase = previous.status.phase if previous and previous.status else None
        current_phase = current.status.phase if current.status else None

        previous_restart = self._restart_count(previous)
        current_restart = self._restart_count(current)

        return PodStateDiff(
            previous_phase=previous_phase,
            current_phase=current_phase,
            phase_changed=previous_phase != current_phase,
            previous_restart_count=previous_restart,
            current_restart_count=current_restart,
            restart_delta=current_restart - previous_restart,
        )

    @staticmethod
    def _restart_count(pod: V1Pod | None) -> int:
        if pod is None or pod.status is None or pod.status.container_statuses is None:
            return 0

        return sum(status.restart_count for status in pod.status.container_statuses)
