from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.exceptions import ApiException

from kubesage.models.container import PodResources
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.utils.exceptions import PodNotFoundError


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_kubernetes_unavailable(
    mock_create_api: MagicMock,
) -> None:
    mock_api = MagicMock()

    mock_api.read_namespaced_pod.side_effect = ApiException(
        reason="Service unavailable"
    )

    mock_create_api.return_value = mock_api

    service = KubernetesService()

    snapshot = service.collect("default", "my-pod")

    assert snapshot.namespace == "default"
    assert snapshot.pod == "my-pod"
    assert snapshot.phase == "Unknown"
    assert snapshot.logs.source == "kubernetes"
    assert snapshot.logs.lines == []
    assert snapshot.containers == []
    assert snapshot.events == []
    assert snapshot.resources == PodResources(containers=[])
    assert snapshot.metrics is None


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
def test_collect_api_error_generic(mock_create_api: MagicMock) -> None:
    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod.side_effect = ApiException(
        status=500, reason="Internal Error"
    )
    mock_create_api.return_value = mock_v1
    service = KubernetesService()

    incident = service.collect("default", "my-pod")

    assert incident.phase == "Unknown"


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_generic_exception(mock_create_api: MagicMock) -> None:
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
    mock_event.last_timestamp = "2026-07-25T12:00:00Z"

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


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
@patch("kubesage.services.kubernetes_service.settings.log_tail_lines", 0)
def test_collect_resources(mock_create_api: MagicMock) -> None:
    mock_v1 = MagicMock()

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
    mock_event.last_timestamp = "2026-07-25T12:00:00Z"

    mock_events_list = MagicMock()
    mock_events_list.items = [mock_event]
    mock_v1.list_namespaced_event.return_value = mock_events_list
    mock_create_api.return_value = mock_v1

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


def test_parse_cpu() -> None:
    service = KubernetesService()
    assert service._parse_cpu("1") == 1
    assert service._parse_cpu("1m") == 0.001
    assert service._parse_cpu(None) is None


def test_parse_memory() -> None:
    service = KubernetesService()
    assert service._parse_memory("1Mi") == 1048576
    assert service._parse_memory("1Gi") == 1073741824
    assert service._parse_memory(None) is None
