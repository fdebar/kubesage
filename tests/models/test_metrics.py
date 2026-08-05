from kubesage.models.metrics import (
    ContainerMetrics,
    PodMetrics,
)


def test_container_metrics() -> None:
    metrics = ContainerMetrics(name="api", cpu_usage=0.1, memory_usage=268435456)

    assert metrics.name == "api"
    assert metrics.cpu_usage == 0.1
    assert metrics.memory_usage == 268435456


def test_pod_metrics() -> None:
    metrics = PodMetrics(
        containers=[ContainerMetrics(name="api", cpu_usage=0.5, memory_usage=100)]
    )

    assert len(metrics.containers) == 1
