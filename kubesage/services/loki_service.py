from typing import Any

import requests
import structlog

from kubesage.models.log import LogSnapshot
from kubesage.services.loki import queries
from kubesage.utils.config import settings

logger = structlog.get_logger()


class LokiService:
    def __init__(self) -> None:
        self.base_url = settings.loki_url

    def query(
        self,
        logql: str,
    ) -> Any:
        try:
            params: dict[str, Any] = {
                "query": logql,
                "limit": settings.loki_query_limit,
            }
            response = requests.get(
                f"{self.base_url}/loki/api/v1/query_range",
                params=params,
                timeout=settings.loki_timeout,
            )
            response.raise_for_status()

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
    ) -> LogSnapshot | None:
        logger.info(
            "loki_collecting_logs",
            namespace=namespace,
            pod=pod,
        )

        payload = self.query(queries.pod_logs(namespace, pod))
        if not payload:
            return None

        lines = self._extract_logs(payload)
        if not lines:
            logger.warning(
                "loki_no_logs_found",
                namespace=namespace,
                pod=pod,
            )

            return None

        logger.info(
            "loki_logs_collected",
            namespace=namespace,
            pod=pod,
            line_count=len(lines),
        )

        return LogSnapshot(
            source="loki",
            lines=lines,
        )

    def _extract_logs(self, payload: dict) -> list[str]:
        lines = []
        for stream in payload["data"]["result"]:
            for _, line in stream["values"]:
                lines.append(line)

        return lines
