from kubesage.models.container import ContainerResources, PodResources
from kubesage.models.kubernetes_snapshot import KubernetesSnapshot
from kubesage.models.log import LogSnapshot


def test_kubernetes_snapshot() -> None:
    snapshot = KubernetesSnapshot(
        namespace="default",
        pod="pod1",
        phase="Running",
        logs=LogSnapshot(
            source="kubernetes",
            lines=["log1", "log2", "log3"],
        ),
        resources=PodResources(
            containers=[
                ContainerResources(
                    name="api",
                    cpu_limit=1.0,
                    memory_limit=1024,
                ),
            ]
        ),
        events=[],
    )

    assert snapshot.namespace == "default"
    assert snapshot.pod == "pod1"
    assert snapshot.phase == "Running"
    assert len(snapshot.events) == 0
    assert snapshot.metrics is None
    assert isinstance(snapshot.resources, PodResources)
    assert isinstance(snapshot.resources.containers[0], ContainerResources)
