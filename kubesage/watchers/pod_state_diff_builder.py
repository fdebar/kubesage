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

        previous_ready = self._is_ready(previous)
        current_ready = self._is_ready(current)

        previous_waiting_reason = self._waiting_reason(previous)
        current_waiting_reason = self._waiting_reason(current)

        oom_killed = self._is_new_oom_killed(previous, current)

        return PodStateDiff(
            previous_phase=previous_phase,
            current_phase=current_phase,
            phase_changed=(previous is not None and previous_phase != current_phase),
            previous_restart_count=previous_restart,
            current_restart_count=current_restart,
            restart_delta=restart_delta,
            previous_waiting_reason=previous_waiting_reason,
            current_waiting_reason=current_waiting_reason,
            previous_ready=previous_ready,
            current_ready=current_ready,
            ready_changed=previous_ready != current_ready,
            waiting_reason_changed=(previous_waiting_reason != current_waiting_reason),
            oom_killed=oom_killed,
        )

    def _is_new_oom_killed(self, previous: V1Pod | None, current: V1Pod) -> bool:
        current_oom_killed = self._is_oom_killed(current)
        if not current_oom_killed:
            return False

        if previous is None:
            return False

        return not self._is_oom_killed(previous)

    @staticmethod
    def _restart_count(pod: V1Pod | None) -> int:
        if pod is None or pod.status is None or pod.status.container_statuses is None:
            return 0

        return sum(status.restart_count for status in pod.status.container_statuses)

    @staticmethod
    def _is_ready(pod: V1Pod | None) -> bool:
        if pod is None or pod.status is None or pod.status.container_statuses is None:
            return False

        statuses = pod.status.container_statuses

        if not statuses:
            return False

        return all(status.ready for status in statuses)

    @staticmethod
    def _waiting_reason(pod: V1Pod | None) -> str | None:
        if pod is None or pod.status is None or pod.status.container_statuses is None:
            return None

        for container in pod.status.container_statuses:
            state = container.state
            if state is None or state.waiting is None:
                continue

            if state.waiting.reason:
                return str(state.waiting.reason)

        return None

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
