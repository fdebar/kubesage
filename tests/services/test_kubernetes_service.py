from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.exceptions import ApiException

from kubesage.services.kubernetes_service import KubernetesService
from kubesage.utils.exceptions import PodNotFoundError


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_pod_not_found(mock_create_api: MagicMock) -> None:
    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod.side_effect = ApiException(
        status=404, reason="Not Found"
    )
    mock_create_api.return_value = mock_v1
    service = KubernetesService()

    with pytest.raises(
        PodNotFoundError, match="Pod 'my-pod' not found in namespace 'default'."
    ):
        service.collect("default", "my-pod")


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_returns_empty_snapshot_on_api_failure(
    mock_create_api: MagicMock,
) -> None:
    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod.side_effect = ApiException(
        status=500, reason="Internal Error"
    )
    mock_create_api.return_value = mock_v1
    service = KubernetesService()

    incident = service.collect("default", "my-pod")

    assert incident.phase == "Unknown"


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_returns_empty_snapshot_on_unexpected_error(
    mock_create_api: MagicMock,
) -> None:
    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod.side_effect = Exception("Some connection issue")
    mock_create_api.return_value = mock_v1
    service = KubernetesService()

    incident = service.collect("default", "my-pod")

    assert incident.phase == "Unknown"


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_success(mock_create_api: MagicMock) -> None:
    mock_v1 = MagicMock()
    mock_create_api.return_value = mock_v1

    # Mock pod_info
    mock_pod = MagicMock()
    mock_pod.status.phase = "Running"

    # Mock container status
    mock_container = MagicMock()
    mock_container.name = "web"
    mock_container.ready = True
    mock_container.restart_count = 3
    mock_container.state.waiting = None
    mock_container.last_state.terminated.exit_code = 137
    mock_container.last_state.terminated.reason = "OOMKilled"

    mock_pod.status.container_statuses = [mock_container]
    mock_v1.read_namespaced_pod.return_value = mock_pod

    # Mock logs
    mock_v1.read_namespaced_pod_log.return_value = b"Hello Logs"

    # Mock events
    mock_event = MagicMock()
    mock_event.type = "Warning"
    mock_event.reason = "FailedScheduling"
    mock_event.message = "0/1 nodes are available"
    mock_event.last_timestamp = datetime(2026, 7, 25, 12, 0, 0, tzinfo=UTC)

    mock_events_list = MagicMock()
    mock_events_list.items = [mock_event]
    mock_v1.list_namespaced_event.return_value = mock_events_list

    service = KubernetesService()

    kubernetes_snapshot = service.collect("default", "my-pod")

    assert kubernetes_snapshot.phase == "Running"
    assert len(kubernetes_snapshot.containers) == 1
    assert kubernetes_snapshot.containers[0].name == "web"
    assert kubernetes_snapshot.containers[0].ready is True
    assert kubernetes_snapshot.containers[0].restart_count == 3
    assert kubernetes_snapshot.containers[0].last_exit_code == 137
    assert kubernetes_snapshot.containers[0].last_exit_reason == "OOMKilled"
    assert kubernetes_snapshot.logs.lines == ["Hello Logs"]
    assert len(kubernetes_snapshot.events) == 1
    assert kubernetes_snapshot.events[0].reason == "FailedScheduling"
    assert kubernetes_snapshot.events[0].message == "0/1 nodes are available"
