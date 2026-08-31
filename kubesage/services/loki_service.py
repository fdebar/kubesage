from datetime import UTC, datetime
from typing import Any

import requests
import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from kubesage.models.log import (
    LogEntry,
    LogQueryType,
    LogSnapshot,
    LogSource,
)
from kubesage.providers.log_provider import LogProvider
from kubesage.services.loki import queries
from kubesage.utils.config import settings

logger = structlog.get_logger()

tracer = trace.get_tracer(__name__)


class LokiService(LogProvider):
    def __init__(self) -> None:
        self.base_url = settings.loki_url
        self.loki_tenant = settings.loki_tenant

    def query(self, logql: str) -> Any:
        with tracer.start_as_current_span("loki.query") as span:
            try:
                params: dict[str, Any] = {
                    "query": logql,
                    "limit": settings.loki_query_limit,
                }
                span.set_attribute("loki.query.limit", settings.loki_query_limit)

                response = requests.get(
                    f"{self.base_url}/loki/api/v1/query_range",
                    params=params,
                    timeout=settings.loki_timeout,
                    headers={"X-Scope-OrgID": self.loki_tenant},
                )
                response.raise_for_status()

                span.set_attribute("http.status_code", response.status_code)

                return response.json()

            except requests.exceptions.ConnectionError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, "Loki server unreachable"))

                logger.warning("loki_server_unreachable_or_offline")
                return {}

            except requests.exceptions.Timeout as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, "Loki query timed out"))

                logger.warning("loki_query_timed_out")
                return {}

            except requests.exceptions.HTTPError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, "Loki returned HTTP error"))

                logger.error(
                    "loki_http_error", status=response.status_code, error=str(exc)
                )
                return {}

            except requests.exceptions.RequestException as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))

                logger.error("Loki query failed: %s", exc)
                return {}

    def collect(
        self,
        namespace: str,
        pod: str,
        query_type: LogQueryType = LogQueryType.ERRORS,
    ) -> LogSnapshot | None:
        with tracer.start_as_current_span("loki.collect") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)
            span.set_attribute("loki.query.type", query_type.value)

            logger.info("loki_collecting_logs", namespace=namespace, pod=pod)

            if query_type == LogQueryType.ERRORS:
                query = queries.pod_errors(namespace, pod)
            elif query_type == LogQueryType.WARNINGS:
                query = queries.pod_warnings(namespace, pod)
            else:
                query = queries.pod_logs(namespace, pod)

            payload = self.query(query)
            if not payload:
                return None

            entries = self._extract_logs(payload)
            if not entries:
                logger.warning("loki_no_logs_found", namespace=namespace, pod=pod)

                return None

            logger.info(
                "loki_logs_collected",
                namespace=namespace,
                pod=pod,
                line_count=len(entries),
            )

            span.set_attribute("loki.logs.count", len(entries))

            return LogSnapshot(source=LogSource.LOKI.value, entries=entries)

    def _extract_logs(self, payload: dict) -> list[LogEntry]:
        entries: list[LogEntry] = []

        results = payload.get("data", {}).get("result", [])
        for stream in results:
            labels = {
                str(key): str(value) for key, value in stream.get("stream", {}).items()
            }

            for timestamp, line in stream.get("values", []):
                entries.append(
                    LogEntry(
                        timestamp=datetime.fromtimestamp(
                            int(timestamp) / 1_000_000_000,
                            tz=UTC,
                        ),
                        message=line,
                        labels=labels,
                    )
                )

        entries.sort(key=lambda entry: entry.timestamp)

        return entries

    def is_available(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/ready",
                timeout=settings.loki_timeout,
            )
            return response.status_code == 200  # type: ignore
        except requests.RequestException:
            return False
