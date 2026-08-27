import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests
import structlog
from opentelemetry import context, trace
from requests import Response

from kubesage.models.container import ContainerUsage
from kubesage.models.prometheus import (
    Metric,
    PrometheusResourceUsage,
    RawPrometheusMetrics,
)
from kubesage.observability.metrics import PROMETHEUS_DURATION
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
tracer = trace.get_tracer(__name__)


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
            return response.status_code == 200  # type: ignore
        except requests.RequestException:
            return False

    def query(self, promql: str) -> list:
        start = time.perf_counter()

        try:
            response = self._request(
                "/api/v1/query",
                params={"query": promql},
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") != "success":
                logger.warning(
                    "prometheus_query_failed",
                    promql=promql,
                    response=payload,
                )
                return []

            result = payload["data"]["result"]

            logger.debug(
                "prometheus_query_result",
                promql=promql,
                result_count=len(result),
            )

            return result  # type: ignore

        except requests.exceptions.ConnectionError:
            logger.warning("prometheus_connection_error", promql=promql)

        except requests.exceptions.Timeout:
            logger.warning("prometheus_query_failed_timeout", promql=promql)

        except requests.exceptions.HTTPError as exc:
            logger.error(
                "prometheus_query_failed_http_error",
                promql=promql,
                code=response.status_code,
                reason=str(exc),
            )

        except requests.exceptions.RequestException as exc:
            logger.error(
                "prometheus_query_request_exception",
                promql=promql,
                error=str(exc),
            )

        except (KeyError, TypeError, ValueError) as exc:
            logger.error(
                "prometheus_invalid_response",
                promql=promql,
                error=str(exc),
            )

        finally:
            PROMETHEUS_DURATION.observe(time.perf_counter() - start)

        return []

    def collect(self, namespace: str, pod: str) -> PrometheusResourceUsage:
        with tracer.start_as_current_span("prometheus.collect") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)

            logger.info(
                "prometheus_starting_collecting_data",
                namespace=namespace,
                pod=pod,
            )

            raw = self.collect_raw_metrics(namespace, pod)

            return PrometheusResourceUsage(
                cpu=self._metric_from_result("cpu", "cores/s", raw.cpu),
                memory=self._metric_from_result("memory", "bytes", raw.memory),
                restarts=self._metric_from_result("restarts", "count", raw.restarts),
                containers=self._container_metrics_from_result(
                    raw.container_cpu,
                    raw.container_memory,
                ),
                cpu_throttling=self._metric_from_result(
                    "cpu_throttling",
                    "ratio",
                    raw.cpu_throttling,
                ),
                network_rx=self._metric_from_result(
                    "network_rx",
                    "bytes/s",
                    raw.network_rx,
                ),
                network_tx=self._metric_from_result(
                    "network_tx",
                    "bytes/s",
                    raw.network_tx,
                ),
                filesystem=self._metric_from_result(
                    "filesystem",
                    "bytes",
                    raw.filesystem,
                ),
            )

    def collect_raw_metrics(self, namespace: str, pod: str) -> RawPrometheusMetrics:
        queries = {
            "cpu": build_query(CPU_QUERY, namespace=namespace, pod=pod),
            "memory": build_query(MEMORY_QUERY, namespace=namespace, pod=pod),
            "container_cpu": build_query(
                CONTAINER_CPU_QUERY, namespace=namespace, pod=pod
            ),
            "container_memory": build_query(
                CONTAINER_MEMORY_QUERY, namespace=namespace, pod=pod
            ),
            "cpu_throttling": build_query(
                CPU_THROTTLING_QUERY, namespace=namespace, pod=pod
            ),
            "restarts": build_query(RESTART_QUERY, namespace=namespace, pod=pod),
            "network_rx": build_query(NETWORK_RX_QUERY, namespace=namespace, pod=pod),
            "network_tx": build_query(NETWORK_TX_QUERY, namespace=namespace, pod=pod),
            "filesystem": build_query(
                FILESYSTEM_USAGE_QUERY, namespace=namespace, pod=pod
            ),
        }

        results: dict[str, list] = {}
        parent_context = context.get_current()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                name: executor.submit(
                    self._query_with_span,
                    name,
                    query,
                    parent_context,
                )
                for name, query in queries.items()
            }
            for name, future in futures.items():
                try:
                    results[name] = future.result()
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "prometheus_metric_collection_failed",
                        metric=name,
                        error=str(exc),
                    )
                    results[name] = []

        return RawPrometheusMetrics(**results)

    def _query_with_span(
        self,
        name: str,
        promql: str,
        parent_context: context.Context,
    ) -> list:
        token = context.attach(parent_context)

        try:
            with tracer.start_as_current_span(f"prometheus.query.{name}") as span:
                result = self.query(promql)
                span.set_attribute("prometheus.query.name", name)
                span.set_attribute("prometheus.query.result_count", len(result))

                return result
        finally:
            context.detach(token)

    def _request(self, path: str, **kwargs: Any) -> Response:
        return self.session.get(
            f"{self.base_url}{path}",
            timeout=settings.prometheus_timeout,
            **kwargs,
        )

    def _container_metrics_from_result(
        self,
        cpu_result: list,
        memory_result: list,
    ) -> list[ContainerUsage]:
        containers: dict[str, ContainerUsage] = {}

        if not cpu_result and not memory_result:
            logger.warning("prometheus_metrics_no_result")

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
