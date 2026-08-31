from datetime import datetime

from kubesage.models.container import ContainerResources, PodResources
from kubesage.models.kubernetes_snapshot import KubernetesSnapshot
from kubesage.models.log import LogEntry, LogSnapshot


def test_kubernetes_snapshot() -> None:
    snapshot = KubernetesSnapshot(
        namespace="default",
        pod="pod1",
        pod_uid="123e4567-e89b-12d3-a456-426614174000",
        phase="Running",
        logs=LogSnapshot(
            source="kubernetes",
            entries=[
                LogEntry(timestamp=datetime.now(), message="log1"),
                LogEntry(timestamp=datetime.now(), message="log2"),
                LogEntry(timestamp=datetime.now(), message="log3"),
            ],
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
