from unittest.mock import MagicMock

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
