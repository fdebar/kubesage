from collections.abc import Iterable

from kubernetes.client import V1Pod

from kubesage.watchers.state_repository import WatcherPodStateRepository


class PodStateCache:
    """
    Stores the latest observed state of each Pod, keyed by Pod UID.
    """

    def __init__(self, repository: WatcherPodStateRepository | None = None) -> None:
        self._repository = repository
        self._pods: dict[str, V1Pod] = {}
        if repository is not None:
            self.replace(repository.list_all(), persist=False)

    def get(self, namespace: str, pod_uid: str) -> V1Pod | None:
        return self._pods.get(self._key(namespace, pod_uid))

    def update(self, pod: V1Pod) -> None:
        metadata = pod.metadata

        if metadata is None:
            return

        if metadata.namespace is None or metadata.uid is None:
            return

        self._pods[self._key(metadata.namespace, metadata.uid)] = pod
        if self._repository is not None:
            self._repository.save(pod)

    def remove(self, namespace: str, pod_uid: str) -> None:
        self._pods.pop(self._key(namespace, pod_uid), None)
        if self._repository is not None:
            self._repository.remove(namespace, pod_uid)

    def replace(self, pods: Iterable[V1Pod], persist: bool = True) -> None:
        new_cache: dict[str, V1Pod] = {}
        pod_list = list(pods)

        for pod in pod_list:
            metadata = pod.metadata

            if metadata is None:
                continue

            if metadata.namespace is None or metadata.uid is None:
                continue

            new_cache[self._key(metadata.namespace, metadata.uid)] = pod

        self._pods = new_cache
        if persist and self._repository is not None:
            self._repository.replace_all(pod_list)

    def size(self) -> int:
        return len(self._pods)

    @staticmethod
    def _key(namespace: str, pod_uid: str) -> str:
        return f"{namespace}/{pod_uid}"
