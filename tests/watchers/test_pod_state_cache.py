from kubernetes.client import V1ObjectMeta, V1Pod

from kubesage.watchers.pod_state_cache import PodStateCache


def build_pod(
    namespace: str = "production",
    name: str = "pod",
    uid: str = "pod-uid",
) -> V1Pod:
    return V1Pod(
        metadata=V1ObjectMeta(
            namespace=namespace,
            name=name,
            uid=uid,
        )
    )


def test_returns_none_when_pod_unknown() -> None:
    cache = PodStateCache()

    assert cache.get("production", "pod") is None


def test_retrieves_a_previously_stored_pod() -> None:
    pod = build_pod()

    cache = PodStateCache()
    cache.update(pod)

    assert cache.get("production", "pod-uid") == pod


def test_update_replaces_previous_state() -> None:
    old_pod = build_pod()
    new_pod = build_pod()

    cache = PodStateCache()
    cache.update(old_pod)
    cache.update(new_pod)

    assert cache.get("production", "pod-uid") == new_pod


def test_remove_deletes_cached_pod() -> None:
    pod = build_pod()

    cache = PodStateCache()
    cache.update(pod)
    cache.remove("production", "pod-uid")

    assert cache.get("production", "pod-uid") is None


def test_retrieves_pod_by_uid() -> None:
    pod = build_pod()

    cache = PodStateCache()
    cache.update(pod)

    assert cache.get("production", "pod-uid") == pod


def test_replace_removes_deleted_pods() -> None:
    old_pod = build_pod(uid="old")
    current_pod = build_pod(uid="current")

    cache = PodStateCache()
    cache.update(old_pod)
    cache.replace([current_pod])

    assert cache.get("production", "old") is None
    assert cache.get("production", "current") == current_pod
