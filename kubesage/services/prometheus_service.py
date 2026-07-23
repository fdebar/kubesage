from kubesage.models.prometheus import Metric
from kubesage.models.prometheus import ResourceUsage
from kubesage.utils.config import settings
import requests
import structlog

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
    ) -> ResourceUsage | None:
        usage = ResourceUsage()
        logger.info("prometheus_collecting_data_for_pod", namespace=namespace, pod=pod)

        cpu = self.query(self.CPU_QUERY % (namespace, pod))
        memory = self.query(self.MEMORY_QUERY % (namespace, pod))
        restarts = self.query(self.RESTART_QUERY % (namespace, pod))
        rx = self.query(self.NETWORK_RX_QUERY % (namespace, pod))
        tx = self.query(self.NETWORK_TX_QUERY % (namespace, pod))

        usage.cpu = self._metric_from_result("cpu", "cores/s", cpu)
        usage.memory = self._metric_from_result("memory", "bytes", memory)
        usage.restarts = self._metric_from_result("restarts", "count", restarts)
        usage.network_rx = self._metric_from_result("network_rx", "bytes/s", rx)
        usage.network_tx = self._metric_from_result("network_tx", "bytes/s", tx)

        if all(
            getattr(usage, field) is None
            for field in ("cpu", "memory", "restarts", "network_rx", "network_tx")
        ):
            logger.warning("prometheus_data_unavailable_continuing_without_metrics")
            return None

        return usage

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

    CPU_QUERY = """
    rate(
    container_cpu_usage_seconds_total{
    namespace="%s",
    pod="%s"
    }[5m]
    )
    """

    MEMORY_QUERY = """
    container_memory_working_set_bytes{
    namespace="%s",
    pod="%s"
    }
    """

    RESTART_QUERY = """
    kube_pod_container_status_restarts_total{
    namespace="%s",
    pod="%s"
    }
    """

    NETWORK_RX_QUERY = """
    rate(
    container_network_receive_bytes_total{
    namespace="%s",
    pod="%s"
    }[5m]
    )
    """

    NETWORK_TX_QUERY = """
    rate(
    container_network_transmit_bytes_total{
    namespace="%s",
    pod="%s"
    }[5m]
    )
    """
