from kubernetes.client import (
    V1ContainerState,
    V1ContainerStateRunning,
    V1ContainerStateTerminated,
    V1ContainerStateWaiting,
    V1ContainerStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodStatus,
)

from kubesage.watchers.pod_state_diff_builder import (
    PodStateDiffBuilder,
)


def make_pod(
    *,
    phase: str = "Running",
    restart_count: int = 0,
    waiting_reason: str | None = None,
    ready: bool = True,
    oom_killed: bool = False,
) -> V1Pod:
    state = (
        V1ContainerState(
            waiting=V1ContainerStateWaiting(
                reason=waiting_reason,
            )
        )
        if waiting_reason
        else V1ContainerState(
            running=V1ContainerStateRunning(
                started_at=None,
            )
        )
    )

    last_state = (
        V1ContainerState(
            terminated=V1ContainerStateTerminated(
                exit_code=137,
                reason="OOMKilled",
            )
        )
        if oom_killed
        else V1ContainerState()
    )

    container = V1ContainerStatus(
        name="app",
        image="busybox",
        image_id="busybox",
        container_id="container",
        ready=ready,
        restart_count=restart_count,
        state=state,
        last_state=last_state,
    )

    return V1Pod(
        metadata=V1ObjectMeta(
            name="test-pod",
            namespace="default",
        ),
        status=V1PodStatus(
            phase=phase,
            container_statuses=[container],
        ),
    )


def test_build_uses_first_snapshot_as_baseline() -> None:
    builder = PodStateDiffBuilder()
    current = make_pod(restart_count=10)
    diff = builder.build(None, current)

    assert diff.previous_restart_count == 10
    assert diff.current_restart_count == 10
    assert diff.restart_delta == 0


def test_build_detects_restart_delta() -> None:
    builder = PodStateDiffBuilder()
    previous = make_pod(restart_count=10)
    current = make_pod(restart_count=11)
    diff = builder.build(previous, current)

    assert diff.restart_delta == 1


def test_build_detects_phase_transition() -> None:
    builder = PodStateDiffBuilder()
    previous = make_pod(phase="Running")
    current = make_pod(phase="Failed")
    diff = builder.build(previous, current)

    assert diff.phase_changed is True
    assert diff.previous_phase == "Running"
    assert diff.current_phase == "Failed"


def test_build_detects_waiting_reason_transition() -> None:
    builder = PodStateDiffBuilder()
    previous = make_pod(waiting_reason=None)
    current = make_pod(waiting_reason="CrashLoopBackOff")
    diff = builder.build(previous, current)

    assert diff.previous_waiting_reason is None
    assert diff.current_waiting_reason == "CrashLoopBackOff"
    assert diff.waiting_reason_changed is True


def test_build_does_not_trigger_oom_on_initial_snapshot() -> None:
    builder = PodStateDiffBuilder()
    current = make_pod(oom_killed=True)
    diff = builder.build(None, current)

    assert diff.oom_killed is False


def test_build_detects_new_oom_event() -> None:
    builder = PodStateDiffBuilder()
    previous = make_pod(oom_killed=False)
    current = make_pod(oom_killed=True)
    diff = builder.build(previous, current)

    assert diff.oom_killed is True


def test_build_does_not_repeat_existing_oom_event() -> None:
    builder = PodStateDiffBuilder()
    previous = make_pod(oom_killed=True)
    current = make_pod(oom_killed=True)
    diff = builder.build(previous, current)

    assert diff.oom_killed is False
