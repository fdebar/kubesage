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

        current_restart = self._restart_count(current)

        if previous is None:
            previous_restart = current_restart
            restart_delta = 0
        else:
            previous_restart = self._restart_count(previous)
            restart_delta = current_restart - previous_restart
        oom_killed = self._is_oom_killed(current)

        return PodStateDiff(
            previous_phase=previous_phase,
            current_phase=current_phase,
            phase_changed=(previous is not None and previous_phase != current_phase),
            previous_restart_count=previous_restart,
            current_restart_count=current_restart,
            restart_delta=restart_delta,
            oom_killed=oom_killed,
        )

    @staticmethod
    def _restart_count(pod: V1Pod | None) -> int:
        if pod is None or pod.status is None or pod.status.container_statuses is None:
            return 0

        return sum(status.restart_count for status in pod.status.container_statuses)

    @staticmethod
    def _is_oom_killed(pod: V1Pod | None) -> bool:
        if pod is None or pod.status is None or pod.status.container_statuses is None:
            return False

        for container in pod.status.container_statuses:
            terminated = (
                container.last_state.terminated if container.last_state else None
            )
            if terminated and terminated.reason == "OOMKilled":
                return True

        return False
