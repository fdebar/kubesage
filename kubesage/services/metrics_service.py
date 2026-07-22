from kubernetes.client.exceptions import ApiException  # type: ignore
from kubesage.utils.kube_client import create_custom_objects_api
from kubesage.observability.factory import get_logger
from kubesage.models.metrics import (
    PodMetrics,
    ContainerMetrics,
)


class MetricsService:
    def __init__(self) -> None:
        self.api = create_custom_objects_api()
        self.logger = get_logger(__name__)

    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> PodMetrics | None:
        self.logger.info("Collecting metrics-server data ...")

        if self.api is None:
            self.logger.warning(
                "Kubernetes unavailable, skipping metrics-server collection."
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
                self.logger.info(
                    "Metrics from metrics-server are not available (pod not found or too recent)."
                )
            elif exc.status == 503:
                self.logger.error("The metrics-server is not yet ready to respond.")
            else:
                self.logger.error(
                    "Kubernetes API Error (%s): %s", exc.status, exc.reason
                )

            return None
        except Exception as exc:
            self.logger.error("Failed to collect metrics-server data: %s", exc)
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
