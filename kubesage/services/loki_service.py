from enum import StrEnum
from typing import Any

import requests
import structlog
from opentelemetry import trace

from kubesage.models.log import LogSnapshot, LogSource
from kubesage.providers.log_provider import LogProvider
from kubesage.services.loki import queries
from kubesage.utils.config import settings

logger = structlog.get_logger()

tracer = trace.get_tracer(__name__)


class LogQueryType(StrEnum):
    ALL = "all"
    ERRORS = "errors"
    WARNINGS = "warnings"


class LokiService(LogProvider):
    def __init__(self) -> None:
        self.base_url = settings.loki_url
        # TODO: We want to keep enable Loki multi-tenant - a configuration must be added
        self.loki_tenant = "kubesage-fake"

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

            except requests.exceptions.ConnectionError:
                logger.warning("loki_server_unreachable_or_offline")
                return {}

            except requests.exceptions.Timeout:
                logger.warning("loki_query_timed_out")
                return {}

            except requests.exceptions.HTTPError as exc:
                logger.error(
                    "Loki returned HTTP error status %s: %s",
                    response.status_code,
                    exc,
                )
                return {}

            except requests.exceptions.RequestException as exc:
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

            lines = self._extract_logs(payload)
            if not lines:
                logger.warning("loki_no_logs_found", namespace=namespace, pod=pod)

                return None

            logger.info(
                "loki_logs_collected",
                namespace=namespace,
                pod=pod,
                line_count=len(lines),
            )

            span.set_attribute("loki.logs.count", len(lines))

            return LogSnapshot(source=LogSource.LOKI.value, lines=lines)

    def _extract_logs(self, payload: dict) -> list[str]:
        lines: list[str] = []

        results = payload.get("data", {}).get("result", [])
        for stream in results:
            for _, line in stream.get("values", []):
                lines.append(line)

        return lines
