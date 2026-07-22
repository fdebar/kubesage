from utils.config import logger
from kubernetes.client.exceptions import ApiException  # type: ignore
from utils.kube_client import create_custom_objects_api

from models.metrics import (
    PodMetrics,
    ContainerMetrics,
)


class MetricsService:
    def __init__(self) -> None:
        self.api = create_custom_objects_api()

    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> PodMetrics | None:
        logger.info("Collecting metrics-server data ...")

        if self.api is None:
            logger.warning(
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
                logger.info(
                    "Metrics from metrics-server are not available (pod not found or too recent)."
                )
            elif exc.status == 503:
                logger.error("The metrics-server is not yet ready to respond.")
            else:
                logger.error("Kubernetes API Error (%s): %s", exc.status, exc.reason)

            return None
        except Exception as exc:
            logger.error("Failed to collect metrics-server data: %s", exc)
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
