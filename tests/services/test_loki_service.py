from datetime import UTC
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from kubesage.models.log import LogQueryType, LogSource
from kubesage.services.loki_service import LokiService


@pytest.fixture
def service() -> LokiService:
    return LokiService()


def _get_loki_span(span_exporter: InMemorySpanExporter) -> ReadableSpan:
    spans = span_exporter.get_finished_spans()

    assert len(spans) == 1
    assert spans[0].name == "loki.query"

    return spans[0]


def test_query_returns_loki_payload(
    service: LokiService, span_exporter: InMemorySpanExporter
) -> None:
    span_exporter.clear()

    payload = {
        "data": {
            "result": [
                {
                    "stream": {"namespace": "default"},
                    "values": [["123456789", "pod started"]],
                }
            ]
        }
    }

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload

    with patch(
        "kubesage.services.loki_service.requests.get", return_value=response
    ) as mock_get:
        result = service.query('{namespace="default"}')

    assert result == payload

    mock_get.assert_called_once()
    response.raise_for_status.assert_called_once()

    span = _get_loki_span(span_exporter)

    assert span.status.is_ok
    if span.attributes:
        assert span.attributes["loki.query.limit"] is not None
        assert span.attributes["http.status_code"] == 200


def test_query_returns_empty_dict_on_connection_error(
    service: LokiService,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    error = requests.exceptions.ConnectionError("Loki unavailable")
    with patch("kubesage.services.loki_service.requests.get", side_effect=error):
        result = service.query('{namespace="default"}')

    assert result == {}

    span = _get_loki_span(span_exporter)

    assert span.status.status_code.name == "ERROR"
    assert len(span.events) == 1
    assert span.events[0].name == "exception"


def test_query_returns_empty_dict_on_timeout(
    service: LokiService, span_exporter: InMemorySpanExporter
) -> None:
    span_exporter.clear()

    error = requests.exceptions.Timeout("Loki timeout")
    with patch("kubesage.services.loki_service.requests.get", side_effect=error):
        result = service.query('{namespace="default"}')

    assert result == {}

    span = _get_loki_span(span_exporter)

    assert span.status.status_code.name == "ERROR"
    assert len(span.events) == 1
    assert span.events[0].name == "exception"


def test_query_returns_empty_dict_on_http_error(
    service: LokiService, span_exporter: InMemorySpanExporter
) -> None:
    span_exporter.clear()

    response = MagicMock()
    response.status_code = 500
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "Internal Server Error"
    )

    with patch("kubesage.services.loki_service.requests.get", return_value=response):
        result = service.query('{namespace="default"}')

    assert result == {}

    span = _get_loki_span(span_exporter)

    assert span.status.status_code.name == "ERROR"
    assert len(span.events) == 1
    assert span.events[0].name == "exception"


def test_query_returns_empty_dict_on_request_error(
    service: LokiService,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    error = requests.exceptions.RequestException("Loki request failed")

    with patch("kubesage.services.loki_service.requests.get", side_effect=error):
        result = service.query('{namespace="default"}')

    assert result == {}

    span = _get_loki_span(span_exporter)

    assert span.status.status_code.name == "ERROR"
    assert len(span.events) == 1
    assert span.events[0].name == "exception"


def test_collect_errors_returns_log_snapshot(
    service: LokiService,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    payload = {
        "data": {
            "result": [
                {
                    "stream": {},
                    "values": [
                        ["123", "ERROR first"],
                        ["456", "ERROR second"],
                    ],
                }
            ]
        }
    }

    with patch.object(service, "query", return_value=payload):
        result = service.collect(
            namespace="default", pod="kubesage-api", query_type=LogQueryType.ERRORS
        )

    assert result is not None
    assert result.source == LogSource.LOKI.value
    assert [entry.message for entry in result.entries] == [
        "ERROR first",
        "ERROR second",
    ]

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "loki.collect"

    if span.attributes:
        assert span.attributes["k8s.namespace"] == "default"
        assert span.attributes["k8s.pod.name"] == "kubesage-api"
        assert span.attributes["loki.query.type"] == LogQueryType.ERRORS.value
        assert span.attributes["loki.logs.count"] == 2


def test_collect_warnings_uses_warning_query(
    service: LokiService,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    payload = {
        "data": {
            "result": [
                {
                    "stream": {},
                    "values": [["123", "WARNING something happened"]],
                }
            ]
        }
    }

    with patch.object(service, "query", return_value=payload) as mock_query:
        result = service.collect(
            namespace="default", pod="kubesage-api", query_type=LogQueryType.WARNINGS
        )

    assert result is not None
    assert [entry.message for entry in result.entries] == [
        "WARNING something happened",
    ]

    mock_query.assert_called_once()

    spans = span_exporter.get_finished_spans()

    assert len(spans) == 1
    span = spans[0]
    assert span.name == "loki.collect"

    if span.attributes:
        assert span.attributes["loki.query.type"] == LogQueryType.WARNINGS.value
        assert span.attributes["loki.logs.count"] == 1


def test_collect_all_uses_all_logs_query(
    service: LokiService,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    payload = {
        "data": {
            "result": [
                {
                    "stream": {},
                    "values": [
                        ["123", "INFO application started"],
                        ["456", "ERROR application failed"],
                    ],
                }
            ]
        }
    }

    with patch.object(service, "query", return_value=payload) as mock_query:
        result = service.collect(
            namespace="default", pod="kubesage-api", query_type=LogQueryType.ALL
        )

    assert result is not None
    assert [entry.message for entry in result.entries] == [
        "INFO application started",
        "ERROR application failed",
    ]

    mock_query.assert_called_once()

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "loki.collect"

    if span.attributes:
        assert span.attributes["loki.query.type"] == LogQueryType.ALL.value
        assert span.attributes["loki.logs.count"] == 2


def test_collect_returns_none_when_query_returns_empty_payload(
    service: LokiService,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    with patch.object(service, "query", return_value={}):
        result = service.collect(namespace="default", pod="kubesage-api")

    assert result is None
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "loki.collect"

    if span.attributes:
        assert span.attributes["k8s.namespace"] == "default"
        assert span.attributes["k8s.pod.name"] == "kubesage-api"
        assert span.attributes["loki.query.type"] == LogQueryType.ERRORS.value


def test_collect_returns_none_when_no_logs_found(
    service: LokiService,
    span_exporter: InMemorySpanExporter,
) -> None:
    span_exporter.clear()

    payload: dict[str, Any] = {"data": {"result": []}}
    with patch.object(service, "query", return_value=payload):
        result = service.collect(namespace="default", pod="kubesage-api")
    assert result is None

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    span = spans[0]
    assert span.name == "loki.collect"

    if span.attributes:
        assert span.attributes["k8s.namespace"] == "default"
        assert span.attributes["k8s.pod.name"] == "kubesage-api"
        assert span.attributes["loki.query.type"] == LogQueryType.ERRORS.value


def test_extract_logs_returns_all_log_entries(service: LokiService) -> None:
    payload = {
        "data": {
            "result": [
                {
                    "stream": {},
                    "values": [
                        ["1756635600000000000", "line one"],
                        ["1756635660000000000", "line two"],
                    ],
                },
                {
                    "stream": {},
                    "values": [["1756635720000000000", "line three"]],
                },
            ]
        }
    }

    result = service._extract_logs(payload)
    assert [entry.message for entry in result] == ["line one", "line two", "line three"]
    assert result[0].timestamp < result[1].timestamp
    assert result[1].timestamp < result[2].timestamp


def test_extract_logs_returns_empty_list_when_no_results(service: LokiService) -> None:
    payload: dict[str, Any] = {"data": {"result": []}}

    result = service._extract_logs(payload)
    assert result == []


def test_extract_logs_preserves_timestamp_and_labels(service: LokiService) -> None:
    payload = {
        "data": {
            "result": [
                {
                    "stream": {
                        "namespace": "default",
                        "pod": "api",
                        "container": "web",
                    },
                    "values": [
                        (
                            "1756635663000000000",
                            "ERROR database connection refused",
                        ),
                    ],
                }
            ]
        }
    }

    entries = service._extract_logs(payload)
    assert len(entries) == 1

    entry = entries[0]
    assert entry.message == "ERROR database connection refused"
    assert entry.timestamp.tzinfo == UTC
    assert entry.labels == {
        "namespace": "default",
        "pod": "api",
        "container": "web",
    }
