from unittest.mock import MagicMock, patch

import pytest
import requests

from kubesage.models.prometheus import Metric
from kubesage.services.prometheus_service import PrometheusService


@patch.object(PrometheusService, "is_available", return_value=False)
def test_collect_when_prometheus_unavailable(
    mock_available: MagicMock,
) -> None:
    service = PrometheusService()

    usage = service.collect("default", "my-pod")

    assert usage is None


@patch("kubesage.services.prometheus_service.requests.get")
def test_query_success(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "success",
        "data": {
            "result": [
                {
                    "metric": {},
                    "value": [1627214400, "0.5"],
                }
            ]
        },
    }
    mock_get.return_value = mock_response
    service = PrometheusService()

    result = service.query("up")

    assert result == [{"metric": {}, "value": [1627214400, "0.5"]}]
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


@patch("kubesage.services.prometheus_service.requests.get")
@pytest.mark.parametrize(
    "exception",
    [
        requests.exceptions.ConnectionError("Connection refused"),
        requests.exceptions.Timeout("Request timed out"),
        requests.exceptions.RequestException("Generic error"),
    ],
)
def test_query_exceptions(mock_get: MagicMock, exception: Exception) -> None:
    mock_get.side_effect = exception
    service = PrometheusService()

    result = service.query("up")

    assert result == []
    mock_get.assert_called_once()


@patch("kubesage.services.prometheus_service.requests.get")
def test_query_http_error(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "Internal Server Error"
    )
    mock_get.return_value = mock_response
    service = PrometheusService()

    result = service.query("up")

    assert result == []
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_metric_from_result_empty() -> None:
    service = PrometheusService()

    metric = service._metric_from_result("cpu", "cores/s", [])

    assert metric is None


def test_metric_from_result_success() -> None:
    service = PrometheusService()
    result = [{"metric": {}, "value": [1627214400.0, "0.75"]}]

    metric = service._metric_from_result("cpu", "cores/s", result)

    assert metric is not None
    assert metric.name == "cpu"
    assert metric.unit == "cores/s"
    assert metric.value == 0.75
    assert metric.timestamp == 1627214400.0


@patch.object(PrometheusService, "query")
def test_collect_metric(mock_query: MagicMock) -> None:
    service = PrometheusService()
    mock_query.return_value = [{"metric": {}, "value": [1627214400.0, "1.5"]}]

    metric = service._collect_metric("cpu", "cores/s", "some_query")

    assert metric is not None
    assert metric.value == 1.5
    mock_query.assert_called_once_with("some_query")


@patch.object(PrometheusService, "is_available", return_value=True)
@patch.object(PrometheusService, "query")
def test_collect_all_none(
    mock_query: MagicMock,
    mock_available: MagicMock,
) -> None:
    service = PrometheusService()
    mock_query.return_value = []

    usage = service.collect("default", "my-pod")

    assert usage is None
    assert mock_query.called


def test_container_metrics_from_result() -> None:
    service = PrometheusService()

    cpu_result = [{"metric": {"container": "api"}, "value": [1000.0, "0.5"]}]
    memory_result = [{"metric": {"container": "api"}, "value": [1000.0, "1048576"]}]

    metrics = service._container_metrics_from_result(cpu_result, memory_result)

    assert len(metrics) == 1
    assert metrics[0].name == "api"
    assert metrics[0].cpu_usage == 0.5
    assert metrics[0].memory_usage == 1048576


@patch.object(PrometheusService, "is_available", return_value=True)
@patch.object(PrometheusService, "query")
def test_collect_success(
    mock_query: MagicMock,
    mock_available: MagicMock,
) -> None:
    service = PrometheusService()
    mock_query.side_effect = [
        [{"metric": {}, "value": [1000.0, "0.1"]}],  # CPU
        [{"metric": {}, "value": [1001.0, "1048576"]}],  # Memory
        [
            {
                "metric": {"container": "api"},
                "value": [1001.5, "0.5"],
            }
        ],  # container CPU
        [
            {
                "metric": {"container": "api"},
                "value": [1001.6, "536870912"],
            }
        ],  # container Memory
        [{"metric": {}, "value": [1002.0, "2"]}],  # CPU throttling
        [{"metric": {}, "value": [1002.0, "2"]}],  # Restart
        [{"metric": {}, "value": [1003.0, "100"]}],  # RX
        [{"metric": {}, "value": [1004.0, "200"]}],  # TX
        [{"metric": {}, "value": [1005.0, "5368709120"]}],  # FS
    ]
    usage = service.collect("default", "my-pod")

    assert usage is not None
    assert isinstance(usage.cpu, Metric)
    assert usage.cpu.value == 0.1
    assert usage.cpu.timestamp == 1000.0

    assert isinstance(usage.memory, Metric)
    assert usage.memory.value == 1048576.0

    assert isinstance(usage.cpu_throttling, Metric)
    assert usage.cpu_throttling.value == 2.0

    assert isinstance(usage.restarts, Metric)
    assert usage.restarts.value == 2.0

    assert len(usage.containers) == 1

    container = usage.containers[0]

    assert container.name == "api"
    assert container.cpu_usage == 0.5
    assert container.memory_usage == 536870912

    assert isinstance(usage.network_rx, Metric)
    assert usage.network_rx.value == 100.0

    assert isinstance(usage.network_tx, Metric)
    assert usage.network_tx.value == 200.0

    assert isinstance(usage.filesystem, Metric)
    assert usage.filesystem.value == 5368709120.0
