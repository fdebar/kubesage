from unittest.mock import MagicMock, patch

import pytest
import requests

from kubesage.models.prometheus import (
    RawPrometheusMetrics,
)
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


@patch.object(PrometheusService, "query")
def test_collect_without_metrics(
    mock_query: MagicMock, service: PrometheusService
) -> None:
    mock_query.return_value = []
    usage = service.collect("default", "my-pod")

    assert usage.cpu is None
    assert usage.memory is None
    assert usage.containers == []


@patch.object(PrometheusService, "query")
def test_collect_raw_metrics(mock_query: MagicMock, service: PrometheusService) -> None:
    mock_query.return_value = []

    raw = service.collect_raw_metrics(
        "default",
        "my-pod",
    )

    assert isinstance(raw, RawPrometheusMetrics)
    assert raw.cpu == []
    assert raw.memory == []
    assert raw.container_cpu == []
    assert mock_query.call_count == 9


@patch.object(PrometheusService, "collect_raw_metrics")
def test_collect_success(mock_collect_raw: MagicMock) -> None:
    service = PrometheusService()

    mock_collect_raw.return_value = RawPrometheusMetrics(
        cpu=[{"metric": {}, "value": [1000.0, "0.1"]}],
        memory=[{"metric": {}, "value": [1001.0, "1048576"]}],
        container_cpu=[{"metric": {"container": "api"}, "value": [1001.5, "0.5"]}],
        container_memory=[
            {"metric": {"container": "api"}, "value": [1001.6, "536870912"]}
        ],
        cpu_throttling=[{"metric": {}, "value": [1002.0, "2"]}],
        restarts=[{"metric": {}, "value": [1002.0, "2"]}],
        network_rx=[{"metric": {}, "value": [1003.0, "100"]}],
        network_tx=[{"metric": {}, "value": [1004.0, "200"]}],
        filesystem=[{"metric": {}, "value": [1005.0, "5368709120"]}],
    )

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
