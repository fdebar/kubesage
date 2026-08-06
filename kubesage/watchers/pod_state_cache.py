from kubernetes.client import V1Pod


class PodStateCache:
    """
    Stores the latest observed state of each pod.
    """

    def __init__(self) -> None:
        self._pods: dict[str, V1Pod] = {}

    def get(self, namespace: str, pod: str) -> V1Pod | None:
        """
        Returns the last known state of a pod.
        """

        return self._pods.get(self._key(namespace, pod))

    def update(self, pod: V1Pod) -> None:
        """
        Stores or replaces the latest pod state.
        """

        metadata = pod.metadata
        if metadata is None:
            return

        self._pods[self._key(metadata.namespace, metadata.name)] = pod

    def remove(self, namespace: str, pod: str) -> None:
        """
        Removes a pod from the cache.
        """

        self._pods.pop(self._key(namespace, pod), None)

    @staticmethod
    def _key(namespace: str, pod: str) -> str:
        return f"{namespace}/{pod}"
