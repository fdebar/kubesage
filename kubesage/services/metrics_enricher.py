from kubesage.models.prometheus import PrometheusResourceUsage
from kubesage.models.resources import PodResources


class MetricsEnricher:
    def enrich(
        self,
        metrics: PrometheusResourceUsage,
        resources: PodResources,
    ) -> PrometheusResourceUsage:
        limits = {container.name: container for container in resources.containers}

        for container_metric in metrics.containers:
            resource = limits.get(container_metric.name)

            if resource is None:
                continue

            container_metric.cpu_limit = resource.cpu_limit

            container_metric.memory_limit = resource.memory_limit

        return metrics
