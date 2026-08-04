from unittest.mock import Mock

from kubernetes.client import V1ObjectMeta, V1Pod

from kubesage.watchers.kubernetes_event_source import (
    KubernetesPodEventSource,
)


def test_watch_returns_pod_event() -> None:
    pod = V1Pod(metadata=V1ObjectMeta(name="api", namespace="default"))
    source = KubernetesPodEventSource.__new__(KubernetesPodEventSource)
    source.api = Mock()
    source.watcher = Mock()
    source.watcher.stream.return_value = iter([{"type": "MODIFIED", "object": pod}])
    events = source.watch()
    event = next(events)

    assert event.type == "MODIFIED"
    assert event.pod.metadata.name == "api"
    assert event.pod.metadata.namespace == "default"
