from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from kubernetes.client import V1ObjectMeta, V1Pod, V1PodStatus

from kubesage.watchers.kubernetes_watcher import KubernetesWatcher
from kubesage.watchers.models.incident_trigger import IncidentTrigger, PodWatchEvent
from kubesage.watchers.models.pod_state_diff import PodStateDiff


@pytest.fixture
def analysis_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def event_filter() -> MagicMock:
    return MagicMock()


@pytest.fixture
def pod_diff() -> PodStateDiff:
    return PodStateDiff(
        previous_phase="Pending",
        current_phase="Running",
        phase_changed=True,
        previous_restart_count=0,
        current_restart_count=1,
        restart_delta=1,
        previous_waiting_reason="Pending",
        current_waiting_reason="Running",
        previous_ready=False,
        current_ready=True,
        ready_changed=True,
        waiting_reason_changed=True,
        oom_killed=False,
    )


@pytest.fixture
def deduplicator() -> MagicMock:
    deduplicator = MagicMock()
    deduplicator.should_process.return_value = True
    return deduplicator


@pytest.fixture
def state_cache() -> MagicMock:
    return MagicMock()


@pytest.fixture
def diff_builder() -> MagicMock:
    return MagicMock()


@pytest.fixture
def watcher(
    analysis_service: MagicMock,
    event_filter: MagicMock,
    deduplicator: MagicMock,
    state_cache: MagicMock,
    diff_builder: MagicMock,
) -> KubernetesWatcher:
    return KubernetesWatcher(
        analysis_service=analysis_service,
        event_filter=event_filter,
        deduplicator=deduplicator,
        state_cache=state_cache,
        diff_builder=diff_builder,
    )


def make_pod(
    name: str = "my-pod", namespace: str = "default", phase: str = "Running"
) -> V1Pod:
    return V1Pod(
        metadata=V1ObjectMeta(
            name=name,
            namespace=namespace,
            uid="123e4567-e89b-12d3-a456-426614174000",
        ),
        status=V1PodStatus(phase=phase),
    )


def make_event(
    pod: V1Pod,
    event_type: str = "MODIFIED",
) -> PodWatchEvent:
    return PodWatchEvent(type=event_type, pod=pod)


def make_trigger(
    reason: str = "CrashLoopBackOff",
    namespace: str = "default",
    pod: str = "my-pod",
) -> IncidentTrigger:
    return IncidentTrigger(
        source="watcher",
        reason=reason,
        namespace=namespace,
        pod=pod,
        pod_uid="123e4567-e89b-12d3-a456-426614174000",
        message="Container entered CrashLoopBackOff",
        occurred_at=datetime.now(UTC),
    )


def test_initial_pods_initialize_state_cache_before_watch(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
) -> None:
    initial_pod = make_pod()
    event_source = MagicMock()
    event_source.initial_pods.return_value = [initial_pod]
    event_source.watch.return_value = []

    watcher.start(event_source)

    event_source.initial_pods.assert_called_once_with()
    state_cache.update.assert_called_once_with(initial_pod)
    event_source.watch.assert_called_once_with()


def test_initial_pods_do_not_trigger_analysis(
    watcher: KubernetesWatcher,
    analysis_service: MagicMock,
    deduplicator: MagicMock,
) -> None:
    initial_pod = make_pod()

    event_source = MagicMock()
    event_source.initial_pods.return_value = [initial_pod]
    event_source.watch.return_value = []

    watcher.start(event_source)

    analysis_service.analyze.assert_not_called()
    deduplicator.should_process.assert_not_called()


def test_non_modified_event_is_ignored(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
) -> None:
    pod = make_pod()
    event = make_event(pod, event_type="ADDED")
    result = watcher._evaluate_event(event)

    assert result is None
    state_cache.get.assert_not_called()
    state_cache.update.assert_not_called()
    diff_builder.build.assert_not_called()
    event_filter.evaluate.assert_not_called()


def test_event_without_metadata_is_ignored(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
) -> None:
    pod = V1Pod(metadata=None, status=V1PodStatus(phase="Running"))
    event = make_event(pod)
    result = watcher._evaluate_event(event)

    assert result is None
    state_cache.get.assert_not_called()
    state_cache.update.assert_not_called()
    diff_builder.build.assert_not_called()
    event_filter.evaluate.assert_not_called()


@pytest.mark.parametrize(
    "namespace,name",
    [
        (None, "my-pod"),
        ("default", None),
        (None, None),
    ],
)
def test_event_without_namespace_or_name_is_ignored(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
    namespace: str,
    name: str,
) -> None:
    pod = V1Pod(
        metadata=V1ObjectMeta(namespace=namespace, name=name),
        status=V1PodStatus(phase="Running"),
    )
    event = make_event(pod)
    result = watcher._evaluate_event(event)

    assert result is None
    state_cache.get.assert_not_called()
    state_cache.update.assert_not_called()
    diff_builder.build.assert_not_called()
    event_filter.evaluate.assert_not_called()


def test_modified_event_builds_diff_updates_cache_and_evaluates_filter(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
    pod_diff: PodStateDiff,
) -> None:
    pod = make_pod()
    previous = make_pod(phase="Pending")

    state_cache.get.return_value = previous
    diff_builder.build.return_value = pod_diff
    event_filter.evaluate.return_value = None

    event = make_event(pod)

    result = watcher._evaluate_event(event)

    assert result is None

    state_cache.get.assert_called_once_with("default", "my-pod")
    diff_builder.build.assert_called_once_with(previous, pod)
    state_cache.update.assert_called_once_with(pod)
    event_filter.evaluate.assert_called_once_with(
        pod_diff,
        "default",
        "my-pod",
        "123e4567-e89b-12d3-a456-426614174000",
    )


def test_modified_event_returns_trigger_from_filter(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
    pod_diff: PodStateDiff,
) -> None:
    pod = make_pod()
    previous = make_pod(phase="Running")
    trigger = make_trigger()

    state_cache.get.return_value = previous
    diff_builder.build.return_value = pod_diff
    event_filter.evaluate.return_value = trigger

    event = make_event(pod)

    result = watcher._evaluate_event(event)

    assert result is trigger

    state_cache.get.assert_called_once_with("default", "my-pod")
    diff_builder.build.assert_called_once_with(previous, pod)
    state_cache.update.assert_called_once_with(pod)
    event_filter.evaluate.assert_called_once_with(
        pod_diff,
        "default",
        "my-pod",
        "123e4567-e89b-12d3-a456-426614174000",
    )


def test_modified_event_with_no_previous_state_is_handled_by_diff_builder(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
    pod_diff: PodStateDiff,
) -> None:
    pod = make_pod()

    state_cache.get.return_value = None
    diff_builder.build.return_value = pod_diff
    event_filter.evaluate.return_value = None

    event = make_event(pod)

    result = watcher._evaluate_event(event)

    assert result is None

    state_cache.get.assert_called_once_with("default", "my-pod")
    diff_builder.build.assert_called_once_with(None, pod)
    state_cache.update.assert_called_once_with(pod)
    event_filter.evaluate.assert_called_once_with(
        pod_diff,
        "default",
        "my-pod",
        "123e4567-e89b-12d3-a456-426614174000",
    )

    def test_all_initial_pods_are_loaded_without_triggering_analysis(
        watcher: KubernetesWatcher,
        state_cache: MagicMock,
        analysis_service: MagicMock,
    ) -> None:
        pods = [
            make_pod(name="kubesage-crashloop"),
            make_pod(name="argocd-applicationset-controller"),
            make_pod(name="healthy-pod"),
        ]

        event_source = MagicMock()
        event_source.initial_pods.return_value = pods
        event_source.watch.return_value = []

        watcher.start(event_source)

        assert state_cache.update.call_count == 3
        state_cache.update.assert_any_call(pods[0])
        state_cache.update.assert_any_call(pods[1])
        state_cache.update.assert_any_call(pods[2])

        analysis_service.analyze.assert_not_called()
