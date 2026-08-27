from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.exceptions import ApiException
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from kubesage.models.container import ContainerResources
from kubesage.models.kubernetes_snapshot import KubernetesSnapshot
from kubesage.services.kubernetes_service import KubernetesService
from kubesage.utils.exceptions import PodNotFoundError


def _get_span(span_exporter: InMemorySpanExporter, name: str) -> Any:
    spans = span_exporter.get_finished_spans()
    matching_spans = [span for span in spans if span.name == name]

    assert matching_spans

    return matching_spans[-1]


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_pod_not_found(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod.side_effect = ApiException(
        status=404,
        reason="Not Found",
    )
    mock_create_api.return_value = mock_v1

    service = KubernetesService()
    with pytest.raises(
        PodNotFoundError, match="Pod 'my-pod' not found in namespace 'default'."
    ):
        service.collect("default", "my-pod")

    span = _get_span(span_exporter, "kubernetes.get_pod")

    assert span.attributes["k8s.namespace"] == "default"
    assert span.attributes["k8s.pod.name"] == "my-pod"
    assert span.status.status_code.name == "ERROR"
    assert any(event.name == "exception" for event in span.events)


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_returns_empty_snapshot_on_api_failure(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod.side_effect = ApiException(
        status=500,
        reason="Internal Error",
    )
    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    snapshot = service.collect("default", "my-pod")

    assert snapshot.phase == "Unknown"

    span = _get_span(span_exporter, "kubernetes.get_pod")

    assert span.status.status_code.name == "ERROR"
    assert any(event.name == "exception" for event in span.events)


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_returns_empty_snapshot_on_unexpected_error(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod.side_effect = Exception("Some connection issue")
    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    snapshot = service.collect("default", "my-pod")

    assert snapshot.phase == "Unknown"

    span = _get_span(span_exporter, "kubernetes.get_pod")

    assert span.status.status_code.name == "ERROR"
    assert len(span.events) == 1
    assert span.events[0].name == "exception"


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_success(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_v1 = MagicMock()
    mock_create_api.return_value = mock_v1

    mock_pod = MagicMock()
    mock_pod.status.phase = "Running"
    mock_pod.metadata.uid = "123e4567-e89b-12d3-a456-426614174000"

    mock_container = MagicMock()
    mock_container.name = "web"
    mock_container.image = "nginx:latest"
    mock_container.ready = True
    mock_container.restart_count = 3
    mock_container.state.waiting = None
    mock_container.last_state.terminated.exit_code = 137
    mock_container.last_state.terminated.reason = "OOMKilled"

    mock_pod.status.container_statuses = [mock_container]

    mock_container_resources = MagicMock()
    mock_container_resources.limits = {
        "cpu": "500m",
        "memory": "256Mi",
    }
    mock_container_resources.requests = {
        "cpu": "100m",
        "memory": "128Mi",
    }

    mock_pod.spec.containers = [
        MagicMock(
            name="web",
            resources=mock_container_resources,
        )
    ]

    mock_v1.read_namespaced_pod.return_value = mock_pod

    mock_v1.read_namespaced_pod_log.return_value = b"Hello Logs"

    mock_event = MagicMock()
    mock_event.type = "Warning"
    mock_event.reason = "FailedScheduling"
    mock_event.message = "0/1 nodes are available"
    mock_event.last_timestamp = datetime(
        2026,
        7,
        25,
        12,
        0,
        0,
        tzinfo=UTC,
    )

    mock_events_list = MagicMock()
    mock_events_list.items = [mock_event]
    mock_v1.list_namespaced_event.return_value = mock_events_list

    service = KubernetesService()

    snapshot = service.collect("default", "my-pod")

    assert snapshot.phase == "Running"

    assert len(snapshot.containers) == 1
    assert snapshot.containers[0].name == "web"
    assert snapshot.containers[0].ready is True
    assert snapshot.containers[0].restart_count == 3
    assert snapshot.containers[0].last_exit_code == 137
    assert snapshot.containers[0].last_exit_reason == "OOMKilled"

    assert snapshot.logs.lines == ["Hello Logs"]

    assert len(snapshot.events) == 1
    assert snapshot.events[0].reason == "FailedScheduling"
    assert snapshot.events[0].message == "0/1 nodes are available"

    spans = span_exporter.get_finished_spans()

    span_names = {span.name for span in spans}

    assert "kubernetes.collect" in span_names
    assert "kubernetes.get_pod" in span_names
    assert "kubernetes.get_logs" in span_names
    assert "kubernetes.get_events" in span_names


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_logs_returns_snapshot(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod_log.return_value = b"line one\nline two"
    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    result = service._collect_logs(
        namespace="default",
        pod="my-pod",
    )

    assert result.lines == ["line one", "line two"]
    assert result.source == "kubernetes"

    span = _get_span(span_exporter, "kubernetes.get_logs")

    assert span.attributes["k8s.namespace"] == "default"
    assert span.attributes["k8s.pod.name"] == "my-pod"
    assert span.status.is_ok


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_logs_returns_empty_snapshot_on_error(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod_log.side_effect = Exception("Logs unavailable")
    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    result = service._collect_logs(
        namespace="default",
        pod="my-pod",
    )

    assert result.lines == []
    assert result.source == "kubernetes"

    span = _get_span(span_exporter, "kubernetes.get_logs")

    assert span.status.status_code.name == "ERROR"
    assert any(event.name == "exception" for event in span.events)


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_logs_raises_pod_not_found(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_v1 = MagicMock()
    mock_v1.read_namespaced_pod_log.side_effect = ApiException(
        status=404,
        reason="Not Found",
    )
    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    with pytest.raises(
        PodNotFoundError,
        match="Pod 'my-pod' not found in namespace 'default'.",
    ):
        service._collect_logs("default", "my-pod")

    span = _get_span(span_exporter, "kubernetes.get_logs")

    assert span.status.status_code.name == "ERROR"
    assert any(event.name == "exception" for event in span.events)


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_events_returns_warning_events(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_event = MagicMock()
    mock_event.type = "Warning"
    mock_event.reason = "BackOff"
    mock_event.message = "Back-off restarting failed container"
    mock_event.last_timestamp = datetime(
        2026,
        7,
        25,
        12,
        0,
        0,
        tzinfo=UTC,
    )

    mock_v1 = MagicMock()
    mock_v1.list_namespaced_event.return_value.items = [mock_event]

    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    result = service._collect_events(
        namespace="default",
        pod="my-pod",
    )

    assert len(result) == 1
    assert result[0].type == "Warning"
    assert result[0].reason == "BackOff"
    assert result[0].message == "Back-off restarting failed container"

    span = _get_span(span_exporter, "kubernetes.get_events")

    assert span.attributes["k8s.namespace"] == "default"
    assert span.attributes["k8s.pod.name"] == "my-pod"
    assert span.status.is_ok


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_events_ignores_normal_events(
    mock_create_api: MagicMock,
) -> None:
    normal_event = MagicMock()
    normal_event.type = "Normal"

    mock_v1 = MagicMock()
    mock_v1.list_namespaced_event.return_value.items = [normal_event]

    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    result = service._collect_events(
        namespace="default",
        pod="my-pod",
    )

    assert result == []


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_events_returns_empty_list_on_api_error(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_v1 = MagicMock()
    mock_v1.list_namespaced_event.side_effect = ApiException(
        status=500,
        reason="Internal Error",
    )
    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    result = service._collect_events(
        namespace="default",
        pod="my-pod",
    )

    assert result == []

    span = _get_span(span_exporter, "kubernetes.get_events")

    assert span.status.status_code.name == "ERROR"
    assert any(event.name == "exception" for event in span.events)


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_collect_events_returns_empty_list_on_unexpected_error(
    mock_create_api: MagicMock,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    mock_v1 = MagicMock()
    mock_v1.list_namespaced_event.side_effect = Exception("Events unavailable")
    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    result = service._collect_events(
        namespace="default",
        pod="my-pod",
    )

    assert result == []

    span = _get_span(span_exporter, "kubernetes.get_events")

    assert span.status.status_code.name == "ERROR"
    assert any(event.name == "exception" for event in span.events)


def test_collect_containers_extracts_container_status() -> None:
    service = KubernetesService.__new__(KubernetesService)

    container = MagicMock()
    container.name = "web"
    container.image = "nginx:latest"
    container.ready = True
    container.restart_count = 4

    container.state.waiting = MagicMock()
    container.state.waiting.reason = "CrashLoopBackOff"
    container.state.waiting.message = "Back-off restarting failed container"

    container.last_state.terminated = MagicMock()
    container.last_state.terminated.exit_code = 137
    container.last_state.terminated.reason = "OOMKilled"

    pod = MagicMock()
    pod.status.container_statuses = [container]

    result = service._collect_containers(pod)

    assert len(result) == 1

    snapshot = result[0]

    assert snapshot.name == "web"
    assert snapshot.image == "nginx:latest"
    assert snapshot.ready is True
    assert snapshot.restart_count == 4
    assert snapshot.waiting_reason == "CrashLoopBackOff"
    assert snapshot.waiting_message == "Back-off restarting failed container"
    assert snapshot.last_exit_code == 137
    assert snapshot.last_exit_reason == "OOMKilled"


def test_collect_containers_handles_missing_statuses() -> None:
    service = KubernetesService.__new__(KubernetesService)

    pod = MagicMock()
    pod.status.container_statuses = None

    result = service._collect_containers(pod)

    assert result == []


def test_collect_resources_extracts_resource_quantities() -> None:
    service = KubernetesService.__new__(KubernetesService)

    resources = MagicMock()
    resources.limits = {
        "cpu": "500m",
        "memory": "256Mi",
    }
    resources.requests = {
        "cpu": "100m",
        "memory": "128Mi",
    }

    container = MagicMock()
    container.name = "web"
    container.resources = resources

    pod = MagicMock()
    pod.spec.containers = [container]

    result = service._collect_resources(pod)

    assert len(result.containers) == 1

    snapshot = result.containers[0]

    assert isinstance(snapshot, ContainerResources)
    assert snapshot.name == "web"
    assert snapshot.cpu_limit == 0.5
    assert snapshot.cpu_request == 0.1
    assert snapshot.memory_limit is not None
    assert snapshot.memory_request is not None


def test_collect_resources_handles_missing_containers() -> None:
    service = KubernetesService.__new__(KubernetesService)

    pod = MagicMock()
    pod.spec.containers = None

    result = service._collect_resources(pod)

    assert result.containers == []


def test_empty_snapshot_contains_expected_defaults() -> None:
    snapshot = KubernetesService._empty_snapshot(
        namespace="default",
        pod="my-pod",
    )

    assert isinstance(snapshot, KubernetesSnapshot)
    assert snapshot.namespace == "default"
    assert snapshot.pod == "my-pod"
    assert snapshot.phase == "Unknown"
    assert snapshot.containers == []
    assert snapshot.events == []
    assert snapshot.logs.lines == []
    assert snapshot.logs.source == "kubernetes"
    assert snapshot.resources.containers == []


@patch("kubesage.services.kubernetes_service.Configuration")
@patch("kubesage.services.kubernetes_service.client.VersionApi")
@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_get_cluster_info(
    mock_create_api: MagicMock,
    mock_version_api: MagicMock,
    mock_configuration: MagicMock,
) -> None:
    mock_v1 = MagicMock()
    mock_create_api.return_value = mock_v1

    mock_configuration.get_default_copy.return_value.host = (
        "https://kubernetes.example.com"
    )

    mock_version_api.return_value.get_code.return_value.git_version = "v1.34.0"

    mock_v1.list_node.return_value.items = [MagicMock(), MagicMock()]
    mock_v1.list_namespace.return_value.items = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]

    service = KubernetesService()

    result = service.get_cluster_info()

    assert result.name == "https://kubernetes.example.com"
    assert result.kubernetes_version == "v1.34.0"
    assert result.node_count == 2
    assert result.namespace_count == 3
    assert result.api_server == "https://kubernetes.example.com"


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_count_nodes(mock_create_api: MagicMock) -> None:
    mock_v1 = MagicMock()
    mock_v1.list_node.return_value.items = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]
    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    assert service.count_nodes() == 3


@patch("kubesage.services.kubernetes_service.create_core_v1_api")
def test_count_pods(mock_create_api: MagicMock) -> None:
    mock_v1 = MagicMock()
    mock_v1.list_pod_for_all_namespaces.return_value.items = [
        MagicMock(),
        MagicMock(),
    ]
    mock_create_api.return_value = mock_v1

    service = KubernetesService()

    assert service.count_pods() == 2
