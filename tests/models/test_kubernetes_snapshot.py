from kubesage.models.container import ContainerInfo
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
        containers=[
            ContainerInfo(
                name="api",
                image="python:3.11-alpine",
                ready=True,
                restart_count=0,
            )
        ],
        events=[],
    )

    assert snapshot.namespace == "default"
    assert snapshot.pod == "pod1"
    assert snapshot.phase == "Running"
    assert len(snapshot.containers) == 1
    assert len(snapshot.events) == 0
    assert snapshot.metrics is None
