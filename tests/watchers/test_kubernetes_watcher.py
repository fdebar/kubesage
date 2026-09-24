from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from kubernetes.client import V1ObjectMeta, V1Pod, V1PodStatus

from kubesage.watchers.event_source import PodListSnapshot
from kubesage.watchers.kubernetes_watcher import KubernetesWatcher
from kubesage.watchers.models.incident_trigger import (
    IncidentTrigger,
    PodWatchEvent,
)
from kubesage.watchers.models.pod_state_diff import PodStateDiff

POD_UID = "123e4567-e89b-12d3-a456-426614174000"
RESOURCE_VERSION = "42"


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
def analysis_submitter() -> MagicMock:
    return MagicMock()


@pytest.fixture
def watcher(
    event_filter: MagicMock,
    deduplicator: MagicMock,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    analysis_submitter: MagicMock,
) -> KubernetesWatcher:
    return KubernetesWatcher(
        event_filter=event_filter,
        deduplicator=deduplicator,
        state_cache=state_cache,
        diff_builder=diff_builder,
        analysis_submitter=analysis_submitter,
    )


def make_pod(
    name: str = "my-pod",
    namespace: str = "default",
    phase: str = "Running",
    uid: str = POD_UID,
    resource_version: str = RESOURCE_VERSION,
) -> V1Pod:
    return V1Pod(
        metadata=V1ObjectMeta(
            name=name,
            namespace=namespace,
            uid=uid,
            resource_version=resource_version,
        ),
        status=V1PodStatus(phase=phase),
    )


def make_event(
    pod: V1Pod,
    event_type: str = "MODIFIED",
    resource_version: str | None = RESOURCE_VERSION,
) -> PodWatchEvent:
    return PodWatchEvent(
        type=event_type,
        pod=pod,
        resource_version=resource_version,
    )


def make_trigger(
    reason: str = "CrashLoopBackOff",
    namespace: str = "default",
    pod: str = "my-pod",
    pod_uid: str = POD_UID,
    resource_version: str = RESOURCE_VERSION,
) -> IncidentTrigger:
    return IncidentTrigger(
        source="watcher",
        reason=reason,
        namespace=namespace,
        pod=pod,
        pod_uid=pod_uid,
        resource_version=resource_version,
        message="Container entered CrashLoopBackOff",
        occurred_at=datetime.now(UTC),
    )


def test_initial_state_initializes_cache_and_starts_watch_from_resource_version(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
) -> None:
    initial_pod = make_pod()

    event_source = MagicMock()
    event_source.initial_state.return_value = MagicMock(
        pods=[initial_pod],
        resource_version="100",
    )
    event_source.watch.return_value = []

    watcher.start(event_source, True)

    event_source.initial_state.assert_called_once_with()

    state_cache.replace.assert_called_once_with([initial_pod])

    event_source.watch.assert_called_once_with("100")


def test_initial_state_does_not_trigger_analysis(
    watcher: KubernetesWatcher,
    analysis_submitter: MagicMock,
    deduplicator: MagicMock,
) -> None:
    initial_pod = make_pod()

    event_source = MagicMock()
    event_source.initial_state.return_value = MagicMock(
        pods=[initial_pod],
        resource_version="100",
    )
    event_source.watch.return_value = []

    watcher.start(event_source, True)

    analysis_submitter.assert_not_called()
    deduplicator.should_process.assert_not_called()


def test_added_event_updates_cache_without_triggering_analysis(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
) -> None:
    pod = make_pod()

    event = make_event(
        pod,
        event_type="ADDED",
    )

    result = watcher._evaluate_event(event)
    assert result is None

    state_cache.update.assert_called_once_with(pod)
    state_cache.get.assert_not_called()
    state_cache.remove.assert_not_called()

    diff_builder.build.assert_not_called()
    event_filter.evaluate.assert_not_called()


def test_deleted_event_removes_pod_from_cache(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
) -> None:
    pod = make_pod()

    event = make_event(
        pod,
        event_type="DELETED",
    )

    result = watcher._evaluate_event(event)
    assert result is None

    state_cache.remove.assert_called_once_with(
        "default",
        POD_UID,
    )

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
    pod = V1Pod(
        metadata=None,
        status=V1PodStatus(phase="Running"),
    )

    event = make_event(pod)

    result = watcher._evaluate_event(event)
    assert result is None

    state_cache.get.assert_not_called()
    state_cache.update.assert_not_called()
    state_cache.remove.assert_not_called()

    diff_builder.build.assert_not_called()
    event_filter.evaluate.assert_not_called()


@pytest.mark.parametrize(
    "namespace,name,uid",
    [
        (None, "my-pod", POD_UID),
        ("default", None, POD_UID),
        ("default", "my-pod", None),
        (None, None, None),
    ],
)
def test_event_without_required_identity_is_ignored(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
    namespace: str | None,
    name: str | None,
    uid: str | None,
) -> None:
    pod = V1Pod(
        metadata=V1ObjectMeta(
            namespace=namespace,
            name=name,
            uid=uid,
            resource_version=RESOURCE_VERSION,
        ),
        status=V1PodStatus(phase="Running"),
    )

    event = make_event(pod)

    result = watcher._evaluate_event(event)

    assert result is None

    state_cache.get.assert_not_called()
    state_cache.update.assert_not_called()
    state_cache.remove.assert_not_called()

    diff_builder.build.assert_not_called()
    event_filter.evaluate.assert_not_called()


def test_event_missing_pod_metadata_resource_version(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
    pod_diff: PodStateDiff,
) -> None:
    pod = make_pod(resource_version="42")
    previous = make_pod(resource_version="41")

    state_cache.get.return_value = previous
    diff_builder.build.return_value = pod_diff
    event_filter.evaluate.return_value = None

    event = make_event(pod, resource_version=None)
    result = watcher._evaluate_event(event)

    assert result is None
    event_filter.evaluate.assert_called_once_with(
        pod_diff,
        "default",
        "my-pod",
        "123e4567-e89b-12d3-a456-426614174000",
        "42",
    )


def test_modified_event_builds_diff_updates_cache_and_evaluates_filter(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
    pod_diff: PodStateDiff,
) -> None:
    pod = make_pod(phase="Running", resource_version="42")
    previous = make_pod(phase="Pending", resource_version="41")

    state_cache.get.return_value = previous
    diff_builder.build.return_value = pod_diff
    event_filter.evaluate.return_value = None

    event = make_event(pod, resource_version="42")
    result = watcher._evaluate_event(event)

    assert result is None

    state_cache.get.assert_called_once_with("default", POD_UID)
    diff_builder.build.assert_called_once_with(previous, pod)
    state_cache.update.assert_called_once_with(pod)
    event_filter.evaluate.assert_called_once_with(
        pod_diff,
        "default",
        "my-pod",
        POD_UID,
        "42",
    )


def test_modified_event_returns_trigger_from_filter(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
    pod_diff: PodStateDiff,
) -> None:
    pod = make_pod(resource_version="42")
    previous = make_pod(phase="Running", resource_version="41")
    trigger = make_trigger(resource_version="42")

    state_cache.get.return_value = previous
    diff_builder.build.return_value = pod_diff
    event_filter.evaluate.return_value = trigger

    event = make_event(pod, resource_version="42")
    result = watcher._evaluate_event(event)

    assert result is trigger

    state_cache.get.assert_called_once_with("default", POD_UID)
    diff_builder.build.assert_called_once_with(previous, pod)
    state_cache.update.assert_called_once_with(pod)
    event_filter.evaluate.assert_called_once_with(
        pod_diff,
        "default",
        "my-pod",
        POD_UID,
        "42",
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

    state_cache.get.assert_called_once_with("default", POD_UID)
    diff_builder.build.assert_called_once_with(None, pod)
    state_cache.update.assert_called_once_with(pod)
    event_filter.evaluate.assert_called_once_with(
        pod_diff,
        "default",
        "my-pod",
        POD_UID,
        RESOURCE_VERSION,
    )


def test_modified_event_uses_event_resource_version_over_pod_metadata(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    diff_builder: MagicMock,
    event_filter: MagicMock,
    pod_diff: PodStateDiff,
) -> None:
    pod = make_pod(resource_version="41")
    state_cache.get.return_value = make_pod(resource_version="40")
    diff_builder.build.return_value = pod_diff
    event_filter.evaluate.return_value = None

    event = make_event(pod, resource_version="42")
    watcher._evaluate_event(event)
    event_filter.evaluate.assert_called_once_with(
        pod_diff,
        "default",
        "my-pod",
        POD_UID,
        "42",
    )


def test_watcher_queues_new_incident(
    watcher: KubernetesWatcher,
    event_filter: MagicMock,
    deduplicator: MagicMock,
    analysis_submitter: MagicMock,
) -> None:
    trigger = make_trigger()

    event_filter.evaluate.return_value = trigger
    deduplicator.should_process.return_value = True

    event_source = MagicMock()
    event_source.initial_state.return_value = MagicMock(
        pods=[],
        resource_version="100",
    )
    event_source.watch.return_value = []

    # We exercise the event-processing path through the watcher.
    # The current implementation consumes events directly from the source,
    # so provide the event through the stream.
    event_source.watch.return_value = iter(
        [
            make_event(
                make_pod(resource_version="101"),
            )
        ]
    )

    watcher.start(event_source, True)
    deduplicator.should_process.assert_called_once_with(trigger)
    analysis_submitter.assert_called_once_with(trigger)


def test_duplicate_incident_is_not_submitted(
    watcher: KubernetesWatcher,
    event_filter: MagicMock,
    deduplicator: MagicMock,
    analysis_submitter: MagicMock,
) -> None:
    trigger = make_trigger()

    event_filter.evaluate.return_value = trigger
    deduplicator.should_process.return_value = False

    event_source = MagicMock()
    event_source.initial_state.return_value = MagicMock(
        pods=[],
        resource_version="100",
    )
    event_source.watch.return_value = iter(
        [
            make_event(
                make_pod(resource_version="101"),
            )
        ]
    )

    watcher.start(event_source, True)
    deduplicator.should_process.assert_called_once_with(trigger)
    analysis_submitter.assert_not_called()


def test_initial_state_loads_all_pods_without_triggering_analysis(
    watcher: KubernetesWatcher,
    state_cache: MagicMock,
    analysis_submitter: MagicMock,
) -> None:
    pods = [
        make_pod(name="kubesage-crashloop", uid="uid-1"),
        make_pod(name="argocd-applicationset-controller", uid="uid-2"),
        make_pod(name="healthy-pod", uid="uid-3"),
    ]

    event_source = MagicMock()
    event_source.initial_state.return_value = MagicMock(
        pods=pods,
        resource_version="100",
    )
    event_source.watch.return_value = []

    watcher.start(event_source, True)

    state_cache.replace.assert_called_once_with(pods)
    analysis_submitter.assert_not_called()


def test_watcher_starts_watch_from_initial_resource_version(
    watcher: KubernetesWatcher,
) -> None:
    initial_pod = make_pod(resource_version="100")

    event_source = MagicMock()
    event_source.initial_state.return_value = PodListSnapshot(
        pods=[initial_pod],
        resource_version="100",
    )
    event_source.watch.return_value = []

    watcher.start(event_source, True)
    event_source.watch.assert_called_once_with("100")
