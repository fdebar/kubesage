import requests
import structlog

from kubesage.models.prometheus import Metric, PrometheusResourceUsage
from kubesage.models.usage import ContainerUsage
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
)
from kubesage.utils.config import settings

logger = structlog.get_logger()


class PrometheusService:
    def __init__(self) -> None:
        self.base_url = settings.prometheus_url

    def query(self, promql: str) -> list:
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/query",
                params={
                    "query": promql,
                },
                timeout=settings.prometheus_timeout,
            )
            response.raise_for_status()

            return response.json()["data"]["result"]  # type: ignore
        except requests.exceptions.ConnectionError:
            logger.warning("prometheus_server_unreachable_or_offline")
            return []
        except requests.exceptions.Timeout:
            logger.warning("prometheus_query_timed_out")
            return []
        except requests.exceptions.HTTPError as exc:
            logger.error(
                "Prometheus returned HTTP error status %s: %s",
                response.status_code,
                exc,
            )
            return []
        except requests.exceptions.RequestException as exc:
            logger.error("Prometheus query failed: %s", exc)
            return []

    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> PrometheusResourceUsage | None:
        logger.info(
            "prometheus_collecting_data_for_pod",
            namespace=namespace,
            pod=pod,
        )

        usage = PrometheusResourceUsage()

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
            return None

        return usage

    def _container_metrics_from_result(
        self,
        cpu_result: list,
        memory_result: list,
    ) -> list[ContainerUsage]:
        containers: dict[str, ContainerUsage] = {}

        logger.debug(
            "prometheus_processing_metrics_results",
            cpu_result=cpu_result,
            memory_result=memory_result,
        )

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

    def collect_container_metrics(
        self,
        namespace: str,
        pod: str,
    ) -> list[ContainerUsage]:
        cpu_result = self.query(
            CONTAINER_CPU_QUERY
            % (
                namespace,
                pod,
            )
        )

        memory_result = self.query(
            CONTAINER_MEMORY_QUERY
            % (
                namespace,
                pod,
            )
        )

        return self._container_metrics_from_result(
            cpu_result,
            memory_result,
        )

    def _metric_from_result(
        self,
        name: str,
        unit: str,
        result: list,
    ) -> Metric | None:
        if not result:
            return None

        timestamp, value = result[0]["value"]

        return Metric(
            name=name,
            value=float(value),
            unit=unit,
            timestamp=float(timestamp),
        )

    def _collect_metric(
        self,
        name: str,
        unit: str,
        query: str,
    ) -> Metric | None:
        result = self.query(query)

        return self._metric_from_result(
            name=name,
            unit=unit,
            result=result,
        )

    def collect_cpu(
        self,
        namespace: str,
        pod: str,
    ) -> Metric | None:
        return self._collect_metric(
            "cpu",
            "cores/s",
            CPU_QUERY % (namespace, pod),
        )

    def collect_memory(
        self,
        namespace: str,
        pod: str,
    ) -> Metric | None:
        return self._collect_metric(
            "memory",
            "bytes",
            MEMORY_QUERY % (namespace, pod),
        )

    def collect_restarts(
        self,
        namespace: str,
        pod: str,
    ) -> Metric | None:
        return self._collect_metric(
            "restarts",
            "count",
            RESTART_QUERY % (namespace, pod),
        )

    def collect_network_rx(
        self,
        namespace: str,
        pod: str,
    ) -> Metric | None:
        return self._collect_metric(
            "network_rx",
            "bytes/s",
            NETWORK_RX_QUERY % (namespace, pod),
        )

    def collect_network_tx(
        self,
        namespace: str,
        pod: str,
    ) -> Metric | None:
        return self._collect_metric(
            "network_tx",
            "bytes/s",
            NETWORK_TX_QUERY % (namespace, pod),
        )

    def collect_filesystem(
        self,
        namespace: str,
        pod: str,
    ) -> Metric | None:
        return self._collect_metric(
            "filesystem",
            "bytes",
            FILESYSTEM_USAGE_QUERY % (namespace, pod),
        )

    def collect_cpu_throttling(
        self,
        namespace: str,
        pod: str,
    ) -> Metric | None:
        return self._collect_metric(
            "cpu_throttling",
            "ratio",
            CPU_THROTTLING_QUERY
            % (
                namespace,
                pod,
                namespace,
                pod,
            ),
        )
