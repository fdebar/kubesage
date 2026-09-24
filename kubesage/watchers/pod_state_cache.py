from collections.abc import Iterable

from kubernetes.client import V1Pod


class PodStateCache:
    """
    Stores the latest observed state of each Pod, keyed by Pod UID.
    """

    def __init__(self) -> None:
        self._pods: dict[str, V1Pod] = {}

    def get(self, namespace: str, pod_uid: str) -> V1Pod | None:
        return self._pods.get(self._key(namespace, pod_uid))

    def update(self, pod: V1Pod) -> None:
        metadata = pod.metadata

        if metadata is None:
            return

        if metadata.namespace is None or metadata.uid is None:
            return

        self._pods[self._key(metadata.namespace, metadata.uid)] = pod

    def remove(self, namespace: str, pod_uid: str) -> None:
        self._pods.pop(self._key(namespace, pod_uid), None)

    def replace(self, pods: Iterable[V1Pod]) -> None:
        new_cache: dict[str, V1Pod] = {}

        for pod in pods:
            metadata = pod.metadata

            if metadata is None:
                continue

            if metadata.namespace is None or metadata.uid is None:
                continue

            new_cache[self._key(metadata.namespace, metadata.uid)] = pod

        self._pods = new_cache

    def size(self) -> int:
        return len(self._pods)

    @staticmethod
    def _key(namespace: str, pod_uid: str) -> str:
        return f"{namespace}/{pod_uid}"
