from unittest.mock import MagicMock

from kubernetes.client import (
    V1ContainerState,
    V1ContainerStateTerminated,
    V1ContainerStatus,
    V1PodStatus,
)
from kubernetes.client.models import V1Pod

from kubesage.watchers.pod_state_diff_builder import PodStateDiffBuilder


def create_mock_pod(
    name: str = "test-pod",
    namespace: str = "default",
    phase: str = "Pending",
    restart_count: int = 0,
) -> V1Pod:
    mock_status = MagicMock()
    mock_status.phase = phase

    mock_container_status = MagicMock()
    mock_container_status.restart_count = restart_count
    mock_status.container_statuses = [mock_container_status]

    mock_pod = MagicMock()
    mock_pod.status = mock_status
    mock_pod.metadata = MagicMock()
    mock_pod.metadata.name = name
    mock_pod.metadata.namespace = namespace

    return mock_pod


def make_pod(*, restart_count: int = 0, oom_killed: bool = False) -> V1Pod:
    last_state = None
    if oom_killed:
        last_state = V1ContainerState(
            terminated=V1ContainerStateTerminated(reason="OOMKilled", exit_code=137)
        )
    container_status = V1ContainerStatus(
        name="app",
        restart_count=restart_count,
        last_state=last_state,
        image="image",
        image_id="image_id",
        ready=False,
    )
    return V1Pod(
        status=V1PodStatus(phase="Running", container_statuses=[container_status])
    )


def test_initial_oom_killed_pod_does_not_trigger_oom() -> None:
    builder = PodStateDiffBuilder()
    current = make_pod(oom_killed=True)
    diff = builder.build(None, current)

    assert diff.oom_killed is False


def test_new_oom_killed_triggers_oom() -> None:
    builder = PodStateDiffBuilder()
    previous = make_pod(oom_killed=False)
    current = make_pod(oom_killed=True)
    diff = builder.build(previous, current)

    assert diff.oom_killed is True


def test_existing_oom_killed_does_not_trigger_again() -> None:
    builder = PodStateDiffBuilder()
    previous = make_pod(oom_killed=True)
    current = make_pod(oom_killed=True)
    diff = builder.build(previous, current)

    assert diff.oom_killed is False


def test_oom_killed_is_cleared_when_current_state_is_not_oom() -> None:
    builder = PodStateDiffBuilder()
    previous = make_pod(oom_killed=True)
    current = make_pod(oom_killed=False)
    diff = builder.build(previous, current)

    assert diff.oom_killed is False


def test_detects_phase_change() -> None:
    builder = PodStateDiffBuilder()

    previous_pod = create_mock_pod(phase="Running")
    current_pod = create_mock_pod(phase="Failed")
    diff = builder.build(previous_pod, current_pod)

    assert diff.phase_changed is True
    assert diff.previous_phase == "Running"
    assert diff.current_phase == "Failed"


def test_no_phase_change() -> None:
    builder = PodStateDiffBuilder()

    previous_pod = create_mock_pod(phase="Running")
    current_pod = create_mock_pod(phase="Running")
    diff = builder.build(previous_pod, current_pod)

    assert diff.phase_changed is False


def test_detects_restart_increment() -> None:
    builder = PodStateDiffBuilder()

    previous_pod = create_mock_pod(restart_count=1)
    current_pod = create_mock_pod(restart_count=3)
    diff = builder.build(previous_pod, current_pod)

    assert diff.restart_delta == 2


def test_initial_pod_with_existing_restarts_does_not_trigger() -> None:
    builder = PodStateDiffBuilder()
    previous = None
    current = create_mock_pod(restart_count=7)

    diff = builder.build(previous, current)

    assert diff.restart_delta == 0
    assert diff.previous_restart_count == 7
    assert diff.current_restart_count == 7
    assert diff.phase_changed is False


def test_restart_after_baseline_is_detected() -> None:
    builder = PodStateDiffBuilder()
    previous = create_mock_pod(restart_count=7)
    current = create_mock_pod(restart_count=8)

    diff = builder.build(previous, current)

    assert diff.restart_delta == 1


def test_unchanged_pod_does_not_trigger() -> None:
    builder = PodStateDiffBuilder()
    previous = create_mock_pod(restart_count=7)
    current = create_mock_pod(restart_count=7)

    diff = builder.build(previous, current)

    assert diff.restart_delta == 0
