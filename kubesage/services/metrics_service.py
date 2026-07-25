import structlog
from kubernetes.client.exceptions import ApiException

from kubesage.models.metrics import (
    ContainerMetrics,
    PodMetrics,
)
from kubesage.providers.metrics_provider import MetricsProvider
from kubesage.utils.kube_client import create_custom_objects_api

logger = structlog.get_logger()


class MetricsService(MetricsProvider):
    def __init__(self) -> None:
        self.api = create_custom_objects_api()

    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> PodMetrics | None:
        logger.info(
            "kubernetes_metrics_collecting_data_for_pod", namespace=namespace, pod=pod
        )

        if self.api is None:
            logger.warning(
                "kubernetes_metrics_unavailable",
                namespace=namespace,
                pod=pod,
            )
            return None

        try:
            metrics = self.api.get_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=namespace,
                plural="pods",
                name=pod,
            )

        except ApiException as exc:
            if exc.status == 404:
                logger.warning(
                    "kubernetes_metrics_not_available_pod_not_found_or_too_recent",
                    namespace=namespace,
                    pod=pod,
                )
            elif exc.status == 503:
                logger.error(
                    "kubernetes_metrics_server_not_yet_ready_to_respond",
                    namespace=namespace,
                    pod=pod,
                )
            else:
                logger.error(
                    "kubernetes_metrics_api_error", status=exc.status, reason=exc.reason
                )

            return None
        except Exception as exc:  # noqa: BLE001
            logger.error("kubernetes_metrics_failed_to_collect_data: %s", exc)
            return None

        result = PodMetrics()
        for container in metrics["containers"]:
            result.containers.append(
                ContainerMetrics(
                    name=container["name"],
                    cpu=container["usage"]["cpu"],
                    memory=container["usage"]["memory"],
                )
            )

        return result
