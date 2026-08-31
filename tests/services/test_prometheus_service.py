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
def test_is_available_returns_false_on_non_200(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_get.return_value = mock_response

    service = PrometheusService()

    assert service.is_available() is False
    mock_get.assert_called_once()


@patch("kubesage.services.prometheus_service.requests.Session.get")
def test_is_available_returns_false_on_request_error(mock_get: MagicMock) -> None:
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

    service = PrometheusService()

    assert service.is_available() is False
    mock_get.assert_called_once()


@patch("kubesage.services.prometheus_service.requests.Session.get")
def test_query_returns_empty_list_on_prometheus_error_status(
    mock_get: MagicMock,
    response: MagicMock,
) -> None:
    response.json.return_value = {
        "status": "error",
        "errorType": "bad_data",
        "error": "invalid query",
    }
    mock_get.return_value = response
    service = PrometheusService()

    assert service.query("invalid") == []


@patch("kubesage.services.prometheus_service.requests.Session.get")
def test_query_returns_empty_list_on_invalid_payload(
    mock_get: MagicMock,
    response: MagicMock,
) -> None:
    response.json.return_value = {
        "status": "success",
        "data": {},
    }
    mock_get.return_value = response
    service = PrometheusService()

    assert service.query("up") == []


@patch("kubesage.services.prometheus_service.PROMETHEUS_DURATION")
@patch("kubesage.services.prometheus_service.requests.Session.get")
def test_query_observes_duration_on_success(
    mock_get: MagicMock,
    mock_duration: MagicMock,
    response: MagicMock,
    metric_result: list[dict],
) -> None:
    response.json.return_value = {
        "status": "success",
        "data": {"result": metric_result},
    }
    mock_get.return_value = response

    service = PrometheusService()

    result = service.query("up")

    assert result == metric_result
    mock_duration.observe.assert_called_once()

    duration = mock_duration.observe.call_args.args[0]
    assert duration >= 0


@patch("kubesage.services.prometheus_service.PROMETHEUS_DURATION")
@patch("kubesage.services.prometheus_service.requests.Session.get")
def test_query_observes_duration_on_error(
    mock_get: MagicMock,
    mock_duration: MagicMock,
) -> None:
    mock_get.side_effect = requests.exceptions.Timeout("timeout")

    service = PrometheusService()

    assert service.query("up") == []

    mock_duration.observe.assert_called_once()

    duration = mock_duration.observe.call_args.args[0]
    assert duration >= 0


@patch.object(PrometheusService, "_query_with_span")
def test_collect_raw_metrics_handles_metric_collection_failure(
    mock_query_with_span: MagicMock,
    service: PrometheusService,
) -> None:
    def side_effect(name: str, promql: str, parent_context: object) -> list:
        if name == "memory":
            raise RuntimeError("Prometheus unavailable")

        return []

    mock_query_with_span.side_effect = side_effect
    raw = service.collect_raw_metrics("default", "my-pod")

    assert isinstance(raw, RawPrometheusMetrics)
    assert raw.cpu == []
    assert raw.memory == []
    assert raw.container_cpu == []


def test_container_metrics_merge_cpu_and_memory(service: PrometheusService) -> None:
    cpu_result = [{"metric": {"container": "api"}, "value": [1000.0, "0.5"]}]
    memory_result = [{"metric": {"container": "api"}, "value": [1000.0, "536870912"]}]

    result = service._container_metrics_from_result(cpu_result, memory_result)

    assert len(result) == 1
    assert result[0].name == "api"
    assert result[0].cpu_usage == 0.5
    assert result[0].memory_usage == 536870912


def test_container_metrics_creates_container_from_memory_only(
    service: PrometheusService,
) -> None:
    memory_result = [{"metric": {"container": "api"}, "value": [1000.0, "536870912"]}]

    result = service._container_metrics_from_result([], memory_result)

    assert len(result) == 1
    assert result[0].name == "api"
    assert result[0].memory_usage == 536870912


def test_container_metrics_ignores_items_without_container(
    service: PrometheusService,
) -> None:
    cpu_result = [{"metric": {}, "value": [1000.0, "0.5"]}]

    result = service._container_metrics_from_result(cpu_result, [])
    assert result == []


def test_metric_from_result_returns_none_when_empty(service: PrometheusService) -> None:
    result = service._metric_from_result("cpu", "cores/s", [])

    assert result is None


def test_time_series_preserves_container_labels(service: PrometheusService) -> None:
    result = [
        {
            "metric": {
                "namespace": "default",
                "pod": "api",
                "container": "web",
            },
            "values": [
                [1756556400, "0.2"],
                [1756556430, "0.4"],
            ],
        }
    ]

    series = service._time_series_from_result(
        name="container_cpu",
        unit="cores",
        result=result,
    )

    assert series[0].labels["container"] == "web"
    assert len(series[0].points) == 2
