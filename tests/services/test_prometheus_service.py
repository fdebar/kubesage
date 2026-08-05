from unittest.mock import MagicMock, patch

import pytest
import requests

from kubesage.models.prometheus import Metric, PrometheusResourceUsage
from kubesage.services.prometheus_service import PrometheusService


@pytest.fixture
def service() -> PrometheusService:
    return PrometheusService()


@pytest.fixture
def response() -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None

    return response


@pytest.fixture
def metric_result() -> list[dict]:
    return [{"metric": {}, "value": [1627214400.0, "0.5"]}]


@pytest.fixture
def container_cpu_result() -> list[dict]:
    return [{"metric": {"container": "api"}, "value": [1000.0, "0.5"]}]


@pytest.fixture
def container_memory_result() -> list[dict]:
    return [{"metric": {"container": "api"}, "value": [1000.0, "536870912"]}]


@pytest.fixture
def collect_results() -> list:
    return [
        [{"metric": {}, "value": [1000.0, "0.1"]}],
        [{"metric": {}, "value": [1001.0, "1048576"]}],
        [{"metric": {"container": "api"}, "value": [1001.5, "0.5"]}],
        [{"metric": {"container": "api"}, "value": [1001.6, "536870912"]}],
        [{"metric": {}, "value": [1002.0, "2"]}],
        [{"metric": {}, "value": [1002.0, "2"]}],
        [{"metric": {}, "value": [1003.0, "100"]}],
        [{"metric": {}, "value": [1004.0, "200"]}],
        [{"metric": {}, "value": [1005.0, "5368709120"]}],
    ]


@patch("kubesage.services.prometheus_service.requests.Session.get")
def test_is_available(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    service = PrometheusService()

    assert service.is_available() is True
    mock_get.assert_called_once()


@patch("kubesage.services.prometheus_service.requests.Session.get")
def test_query_success(
    mock_get: MagicMock,
    service: PrometheusService,
    response: MagicMock,
    metric_result: list[dict],
) -> None:
    response.json.return_value = {
        "status": "success",
        "data": {"result": metric_result},
    }
    mock_get.return_value = response

    assert service.query("up") == metric_result


@patch("kubesage.services.prometheus_service.requests.Session.get")
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


@patch("kubesage.services.prometheus_service.requests.Session.get")
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


def test_metric_from_result(
    service: PrometheusService, metric_result: list[dict]
) -> None:
    metric = service._metric_from_result(
        "cpu",
        "cores/s",
        metric_result,
    )

    assert metric == Metric(
        name="cpu",
        value=0.5,
        unit="cores/s",
        timestamp=1627214400.0,
    )


def test_container_metrics_from_result(
    service: PrometheusService,
    container_cpu_result: list[dict],
    container_memory_result: list[dict],
) -> None:
    metrics = service._container_metrics_from_result(
        container_cpu_result,
        container_memory_result,
    )

    assert len(metrics) == 1
    assert metrics[0].name == "api"
    assert metrics[0].cpu_usage == 0.5
    assert metrics[0].memory_usage == 536870912


@patch.object(PrometheusService, "query")
def test_collect_all_none(
    mock_query: MagicMock,
    service: PrometheusService,
) -> None:
    mock_query.return_value = []

    assert service.collect("default", "my-pod") == PrometheusResourceUsage()
    assert mock_query.call_count == 9


@patch.object(PrometheusService, "query")
def test_collect_success(
    mock_query: MagicMock,
    service: PrometheusService,
    collect_results: list,
) -> None:
    mock_query.side_effect = collect_results
    usage = service.collect("default", "my-pod")

    assert usage is not None
    assert usage.cpu is not None
    assert usage.memory is not None
    assert usage.network_rx is not None
    assert usage.network_tx is not None
    assert usage.filesystem is not None

    assert usage.cpu.value == 0.1
    assert usage.memory.value == 1048576
    assert usage.network_rx.value == 100
    assert usage.network_tx.value == 200
    assert usage.filesystem.value == 5368709120
    assert len(usage.containers) == 1

    assert mock_query.call_count == 9
