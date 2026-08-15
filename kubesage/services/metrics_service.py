import structlog
from kubernetes.client.exceptions import ApiException
from opentelemetry import trace

from kubesage.models.metrics import (
    ContainerMetrics,
    PodMetrics,
)
from kubesage.providers.metrics_provider import MetricsProvider
from kubesage.utils.kube_client import create_custom_objects_api
from kubesage.utils.resource_quantity import parse_cpu_quantity, parse_memory_quantity

logger = structlog.get_logger()

tracer = trace.get_tracer(__name__)


class MetricsService(MetricsProvider):
    """Metrics Service to collect metrics from metrics.k8s.io."""

    def __init__(self) -> None:
        self.api = create_custom_objects_api()
        self._available: bool = self.api is not None

    def collect(self, namespace: str, pod: str) -> PodMetrics | None:
        with tracer.start_as_current_span("metrics.collect") as span:
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)

            if not self._available:
                logger.info(
                    "kubernetes_metrics_unavailable",
                    namespace=namespace,
                    pod=pod,
                )
                return None

            try:
                logger.info(
                    "kubernetes_metrics_start_collect",
                    namespace=namespace,
                    pod=pod,
                )

                with tracer.start_as_current_span(
                    "metrics.k8s.get_pod_metrics"
                ) as metrics_span:
                    metrics_span.set_attribute("k8s.namespace", namespace)
                    metrics_span.set_attribute("k8s.pod.name", pod)

                    metrics = self.api.get_namespaced_custom_object(
                        group="metrics.k8s.io",
                        version="v1beta1",
                        namespace=namespace,
                        plural="pods",
                        name=pod,
                    )

            except ApiException as exc:
                span.record_exception(exc)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))

                if exc.status in (404, 503):
                    self._available = False

                logger.warning(
                    "kubernetes_metrics_unavailable",
                    namespace=namespace,
                    pod=pod,
                    status=exc.status,
                    reason=exc.reason,
                )
                return None

            except Exception as exc:  # noqa: BLE001
                span.record_exception(exc)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
                logger.warning(
                    "kubernetes_metrics_collection_failed",
                    namespace=namespace,
                    pod=pod,
                    exc=exc,
                )
                return None

            if not isinstance(metrics, dict):
                logger.warning(
                    "kubernetes_metrics_invalid_response", namespace=namespace, pod=pod
                )
                return None

            result = PodMetrics()

            for container in metrics.get("containers", []):
                usage = container.get("usage", {})
                result.containers.append(
                    ContainerMetrics(
                        name=container["name"],
                        cpu_usage=parse_cpu_quantity(usage.get("cpu", "0")),
                        memory_usage=parse_memory_quantity(usage.get("memory", "0")),
                    )
                )

            return result
