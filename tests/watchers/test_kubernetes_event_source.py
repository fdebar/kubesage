from unittest.mock import Mock

import pytest
from kubernetes.client import V1ObjectMeta, V1Pod

from kubesage.watchers.kubernetes_event_source import (
    KubernetesPodEventSource,
    WatchExpiredError,
)


def test_watch_returns_pod_event() -> None:
    pod = V1Pod(metadata=V1ObjectMeta(name="api", namespace="default"))
    source = KubernetesPodEventSource.__new__(KubernetesPodEventSource)
    source.api = Mock()
    source.watcher = Mock()
    source.watcher.stream.return_value = iter([{"type": "MODIFIED", "object": pod}])
    events = source.watch(resource_version="123e4567-e89b-12d3-a456-426614174000")
    event = next(events)

    assert event.type == "MODIFIED"
    assert event.pod.metadata.name == "api"
    assert event.pod.metadata.namespace == "default"


def test_watch_passes_resource_version_to_stream() -> None:
    source = KubernetesPodEventSource.__new__(KubernetesPodEventSource)

    source.api = Mock()
    source.watcher = Mock()

    pod = V1Pod(
        metadata=V1ObjectMeta(
            name="api",
            namespace="default",
            uid="uid-1",
            resource_version="42",
        )
    )

    source.watcher.stream.return_value = iter(
        [
            {
                "type": "MODIFIED",
                "object": pod,
            }
        ]
    )

    events = list(source.watch("41"))
    source.watcher.stream.assert_called_once()
    kwargs = source.watcher.stream.call_args.kwargs

    assert kwargs["resource_version"] == "41"
    assert events[0].resource_version == "42"


def test_410_raises_watch_expired_error() -> None:
    source = KubernetesPodEventSource.__new__(KubernetesPodEventSource)
    source.api = Mock()
    source.watcher = Mock()

    source.watcher.stream.return_value = iter(
        [
            {
                "type": "ERROR",
                "object": {
                    "code": 410,
                },
            }
        ]
    )

    with pytest.raises(WatchExpiredError):
        list(source.watch("41"))
