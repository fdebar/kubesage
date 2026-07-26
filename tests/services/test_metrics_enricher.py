from kubesage.models.metrics import ContainerMetrics
from kubesage.models.prometheus import PrometheusResourceUsage
from kubesage.models.resources import (
    ContainerResourceLimits,
    PodResources,
)
from kubesage.services.metrics_enricher import MetricsEnricher


def test_enrich_container_metrics() -> None:
    metrics = PrometheusResourceUsage(
        containers=[
            ContainerMetrics(
                name="api",
                cpu_usage=0.8,
                memory_usage=900,
            )
        ]
    )

    resources = PodResources(
        containers=[
            ContainerResourceLimits(
                name="api",
                cpu_limit=1.0,
                memory_limit=1000,
            )
        ]
    )

    enriched = MetricsEnricher().enrich(
        metrics,
        resources,
    )
    container = enriched.containers[0]

    assert container.cpu_limit == 1.0
    assert container.memory_limit == 1000
