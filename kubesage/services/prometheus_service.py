from typing import Any

import requests
import structlog
from requests import Response

from kubesage.models.container import ContainerUsage
from kubesage.models.prometheus import Metric, PrometheusResourceUsage
from kubesage.services.prometheus.queries import (
    CONTAINER_CPU_QUERY,
    CONTAINER_MEMORY_QUERY,
    CPU_QUERY,
    CPU_THROTTLING_QUERY,
    FILESYSTEM_USAGE_QUERY,
    MEMORY_QUERY,
    NETWORK_RX_QUERY,
    NETWORK_TX_QUERY,
    RESTART_QUERY,
    build_query,
)
from kubesage.utils.config import settings

logger = structlog.get_logger()


class PrometheusService:
    """
    Service to collect metrics from Prometheus.

    This class provides methods to collect metrics from Prometheus and
    return them in a structured format.
    """

    def __init__(self) -> None:
        self.base_url = settings.prometheus_url
        self.session = requests.Session()

    def is_available(self) -> bool:
        try:
            response = self._request("/-/ready")
            return bool(response.status_code == 200)
        except requests.RequestException:
            return False

    def query(self, promql: str) -> list:
        try:
            response = self._request(
                "/api/v1/query",
                params={"query": promql},
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") != "success":
                logger.warning("prometheus_query_failed", response=payload)
                return []

            return payload["data"]["result"]  # type: ignore
        except requests.exceptions.ConnectionError:
            logger.warning("prometheus_connection_error", promql=promql)
        except requests.exceptions.Timeout:
            logger.warning("prometheus_query_failed_timeout", promql=promql)
        except requests.exceptions.HTTPError as exc:
            logger.error(
                "prometheus_query_failed_http_error",
                code=response.status_code,
                reason=exc,
            )
        except requests.exceptions.RequestException as exc:
            logger.error("prometheus_query_request_exception", exc=exc)

        return []

    def collect(self, namespace: str, pod: str) -> PrometheusResourceUsage:
        logger.info("prometheus_starting_collecting_data", namespace=namespace, pod=pod)

        usage = PrometheusResourceUsage(containers=[])

        usage.cpu = self.collect_cpu(namespace, pod)
        usage.memory = self.collect_memory(namespace, pod)
        usage.containers = self.collect_container_metrics(namespace, pod)
        usage.cpu_throttling = self.collect_cpu_throttling(namespace, pod)
        usage.restarts = self.collect_restarts(namespace, pod)
        usage.network_rx = self.collect_network_rx(namespace, pod)
        usage.network_tx = self.collect_network_tx(namespace, pod)
        usage.filesystem = self.collect_filesystem(namespace, pod)

        if (
            all(
                metric is None
                for metric in (
                    usage.cpu,
                    usage.memory,
                    usage.cpu_throttling,
                    usage.restarts,
                    usage.network_rx,
                    usage.network_tx,
                    usage.filesystem,
                )
            )
            and len(usage.containers) == 0
        ):
            logger.warning("prometheus_data_unavailable_continuing_without_metrics")

        return usage

    def collect_raw_metrics(self, namespace: str, pod: str) -> dict[str, list]:
        queries = {
            "cpu": build_query(
                CPU_QUERY,
                namespace=namespace,
                pod=pod,
            ),
            "memory": build_query(
                MEMORY_QUERY,
                namespace=namespace,
                pod=pod,
            ),
            "restart": build_query(
                RESTART_QUERY,
                namespace=namespace,
                pod=pod,
            ),
        }

        return {name: self.query(query) for name, query in queries.items()}

    def collect_container_metrics(
        self, namespace: str, pod: str
    ) -> list[ContainerUsage]:
        cpu_result = self.query(
            build_query(CONTAINER_CPU_QUERY, namespace=namespace, pod=pod)
        )
        memory_result = self.query(
            build_query(CONTAINER_MEMORY_QUERY, namespace=namespace, pod=pod)
        )

        return self._container_metrics_from_result(cpu_result, memory_result)

    def collect_cpu(self, namespace: str, pod: str) -> Metric | None:
        return self._collect_metric(
            "cpu",
            "cores/s",
            build_query(
                CPU_QUERY,
                namespace=namespace,
                pod=pod,
            ),
        )

    def collect_memory(self, namespace: str, pod: str) -> Metric | None:
        return self._collect_metric(
            "memory",
            "bytes",
            build_query(
                MEMORY_QUERY,
                namespace=namespace,
                pod=pod,
            ),
        )

    def collect_restarts(self, namespace: str, pod: str) -> Metric | None:
        return self._collect_metric(
            "restarts",
            "count",
            build_query(
                RESTART_QUERY,
                namespace=namespace,
                pod=pod,
            ),
        )

    def collect_network_rx(self, namespace: str, pod: str) -> Metric | None:
        return self._collect_metric(
            "network_rx",
            "bytes/s",
            build_query(
                NETWORK_RX_QUERY,
                namespace=namespace,
                pod=pod,
            ),
        )

    def collect_network_tx(self, namespace: str, pod: str) -> Metric | None:
        return self._collect_metric(
            "network_tx",
            "bytes/s",
            build_query(
                NETWORK_TX_QUERY,
                namespace=namespace,
                pod=pod,
            ),
        )

    def collect_filesystem(self, namespace: str, pod: str) -> Metric | None:
        return self._collect_metric(
            "filesystem",
            "bytes",
            build_query(
                FILESYSTEM_USAGE_QUERY,
                namespace=namespace,
                pod=pod,
            ),
        )

    def collect_cpu_throttling(self, namespace: str, pod: str) -> Metric | None:
        return self._collect_metric(
            "cpu_throttling",
            "ratio",
            build_query(
                CPU_THROTTLING_QUERY,
                namespace=namespace,
                pod=pod,
            ),
        )

    def _request(self, url: str, **kwargs: Any) -> Response:
        return self.session.get(url, timeout=settings.prometheus_timeout, **kwargs)

    def _container_metrics_from_result(
        self, cpu_result: list, memory_result: list
    ) -> list[ContainerUsage]:
        containers: dict[str, ContainerUsage] = {}

        if not cpu_result and not memory_result:
            logger.warning("prometheus_metrics_unavailable")

        for item in cpu_result:
            name = item["metric"].get("container")
            if not name:
                continue
            _, value = item["value"]
            containers[name] = ContainerUsage(
                name=name,
                cpu_usage=float(value),
            )

        for item in memory_result:
            name = item["metric"].get("container")
            if not name:
                continue
            _, value = item["value"]
            if name not in containers:
                containers[name] = ContainerUsage(
                    name=name,
                )

            containers[name].memory_usage = int(float(value))

        return list(containers.values())

    def _metric_from_result(self, name: str, unit: str, result: list) -> Metric | None:
        if not result:
            return None

        timestamp, value = result[0]["value"]

        return Metric(
            name=name,
            value=float(value),
            unit=unit,
            timestamp=float(timestamp),
        )

    def _collect_metric(self, name: str, unit: str, query: str) -> Metric | None:
        result = self.query(query)

        return self._metric_from_result(
            name=name,
            unit=unit,
            result=result,
        )
