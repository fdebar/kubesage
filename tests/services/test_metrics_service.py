from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.exceptions import ApiException

from kubesage.services.metrics_service import MetricsService


@patch("kubesage.services.metrics_service.create_custom_objects_api")
def test_collect_metrics_unavailable(mock_create_api: MagicMock) -> None:
    mock_create_api.return_value = None
    service = MetricsService()

    metrics = service.collect("default", "my-pod")

    assert metrics is None


@patch("kubesage.services.metrics_service.create_custom_objects_api")
@pytest.mark.parametrize("status_code", [404, 503, 500])
def test_collect_api_errors(mock_create_api: MagicMock, status_code: int) -> None:
    mock_api = MagicMock()
    mock_api.get_namespaced_custom_object.side_effect = ApiException(
        status=status_code, reason="Error"
    )
    mock_create_api.return_value = mock_api
    service = MetricsService()

    metrics = service.collect("default", "my-pod")

    assert metrics is None


@patch("kubesage.services.metrics_service.create_custom_objects_api")
def test_collect_generic_exception(mock_create_api: MagicMock) -> None:
    mock_api = MagicMock()
    mock_api.get_namespaced_custom_object.side_effect = Exception("General error")
    mock_create_api.return_value = mock_api
    service = MetricsService()

    metrics = service.collect("default", "my-pod")

    assert metrics is None


@patch("kubesage.services.metrics_service.create_custom_objects_api")
def test_collect_success(mock_create_api: MagicMock) -> None:
    mock_api = MagicMock()
    mock_api.get_namespaced_custom_object.return_value = {
        "containers": [
            {
                "name": "web",
                "usage": {
                    "cpu": "100m",
                    "memory": "256Mi",
                },
            }
        ]
    }
    mock_create_api.return_value = mock_api
    service = MetricsService()

    metrics = service.collect("default", "my-pod")

    assert metrics is not None
    assert len(metrics.containers) == 1
    assert metrics.containers[0].name == "web"
    assert metrics.containers[0].cpu_usage == "100m"
    assert metrics.containers[0].memory_usage == "256Mi"
