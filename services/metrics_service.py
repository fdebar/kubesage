from config import logger
from kubernetes.client.exceptions import ApiException  # type: ignore
from kubernetes import client, config  # type: ignore

from models.metrics import (
    PodMetrics,
    ContainerMetrics,
)


class MetricsService:
    def __init__(self) -> None:

        config.load_kube_config()
        self.api = client.CustomObjectsApi()

    def collect(
        self,
        namespace: str,
        pod: str,
    ) -> PodMetrics | None:
        logger.info("Collecting metrics-server data ...")

        try:
            metrics = self.api.get_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=namespace,
                plural="pods",
                name=pod,
            )

        except ApiException as e:
            if e.status == 404:
                logger.info(
                    "Metrics from metrics-server are not available (pod not found or too recent)."
                )
            elif e.status == 503:
                logger.error("The metrics-server is not yet ready to respond.")
            else:
                logger.error(f"Kubernetes API Error ({e.status}) : {e.reason}")

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
