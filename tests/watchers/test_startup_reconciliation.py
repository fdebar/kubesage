from unittest.mock import Mock

from kubernetes.client import (
    V1ContainerState,
    V1ContainerStateRunning,
    V1ContainerStateWaiting,
    V1ContainerStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodStatus,
)

from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.kubernetes_watcher import KubernetesWatcher
from kubesage.watchers.pod_event_filter import PodEventFilter
from kubesage.watchers.pod_state_cache import PodStateCache
from kubesage.watchers.pod_state_diff_builder import PodStateDiffBuilder


def make_pod(waiting_reason: str | None = None) -> V1Pod:
    state = (
        V1ContainerState(waiting=V1ContainerStateWaiting(reason=waiting_reason))
        if waiting_reason
        else V1ContainerState(running=V1ContainerStateRunning())
    )
    return V1Pod(
        metadata=V1ObjectMeta(
            name="api",
            namespace="production",
            uid="pod-uid",
            resource_version="42",
        ),
        status=V1PodStatus(
            phase="Running",
            container_statuses=[
                V1ContainerStatus(
                    name="app",
                    image="example/api:latest",
                    image_id="sha256:abc",
                    ready=waiting_reason is None,
                    restart_count=2,
                    state=state,
                )
            ],
        ),
    )


def make_watcher(cache: PodStateCache, submit: Mock) -> KubernetesWatcher:
    return KubernetesWatcher(
        event_filter=PodEventFilter(),
        deduplicator=IncidentDeduplicator(),
        state_cache=cache,
        diff_builder=PodStateDiffBuilder(),
        analysis_submitter=submit,
    )


def test_startup_reconciliation_analyzes_new_incident_transition() -> None:
    cache = PodStateCache()
    cache.update(make_pod())
    submit = Mock()
    watcher = make_watcher(cache, submit)

    watcher._reconcile_startup([make_pod(waiting_reason="CrashLoopBackOff")])

    submit.assert_called_once()
    assert submit.call_args.args[0].reason == "CrashLoopBackOff"


def test_startup_reconciliation_ignores_unchanged_incident_state() -> None:
    crashloop_pod = make_pod(waiting_reason="CrashLoopBackOff")
    cache = PodStateCache()
    cache.update(crashloop_pod)

    submit = Mock()

    watcher = make_watcher(cache, submit)
    watcher._reconcile_startup([crashloop_pod])

    submit.assert_not_called()
