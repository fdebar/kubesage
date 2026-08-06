from kubernetes.client import V1ObjectMeta, V1Pod

from kubesage.watchers.pod_state_cache import PodStateCache


def build_pod(namespace: str = "production", name: str = "pod") -> V1Pod:
    return V1Pod(
        metadata=V1ObjectMeta(
            namespace=namespace,
            name=name,
        )
    )


def test_returns_none_when_pod_unknown() -> None:
    cache = PodStateCache()

    assert cache.get("production", "pod") is None


def test_retrieves_a_previously_stored_pod() -> None:
    cache = PodStateCache()
    pod = build_pod()
    cache.update(pod)

    assert cache.get("production", "pod") == pod


def test_update_replaces_previous_state() -> None:
    old_pod = build_pod("production", "pod")
    new_pod = build_pod("production", "pod")

    cache = PodStateCache()
    cache.update(old_pod)
    cache.update(new_pod)

    assert cache.get("production", "pod") == new_pod


def test_remove_deletes_cached_pod() -> None:
    cache = PodStateCache()
    pod = build_pod()

    cache.update(pod)
    cache.remove("production", "pod")

    assert cache.get("production", "pod") is None
