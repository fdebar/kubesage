from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import Mock

from kubernetes.client import (
    V1ContainerState,
    V1ContainerStateWaiting,
    V1ContainerStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodStatus,
)

from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.kubernetes_watcher import KubernetesWatcher
from kubesage.watchers.models.incident_trigger import (
    IncidentTrigger,
    PodWatchEvent,
)
from kubesage.watchers.pod_event_filter import PodEventFilter
from kubesage.watchers.pod_state_cache import PodStateCache
from kubesage.watchers.pod_state_diff_builder import PodStateDiffBuilder
from tests.watchers.test_pod_event_filter import build_event, build_pod


class FakeEventSource:
    def __init__(self, event: PodWatchEvent) -> None:
        self.event = event

    def watch(self) -> Iterator[PodWatchEvent]:
        yield self.event

    def initial_pods(self) -> Iterator[V1Pod]:
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="payment-api",
                namespace="production",
            ),
            status=V1PodStatus(
                container_statuses=[
                    V1ContainerStatus(
                        name="payment",
                        image="payment:v1",
                        state=V1ContainerState(
                            waiting=V1ContainerStateWaiting,
                        ),
                        image_id="image_id",
                        ready=True,
                        restart_count=0,
                    )
                ]
            ),
        )

        yield pod


def test_watcher_triggers_analysis() -> None:
    analysis_service = Mock()
    expected_analysis = Mock(spec=Analysis)
    analysis_service.analyze.return_value = expected_analysis

    watcher = KubernetesWatcher(
        analysis_service=analysis_service,
        event_filter=PodEventFilter(),
        deduplicator=IncidentDeduplicator(),
        state_cache=PodStateCache(),
        diff_builder=PodStateDiffBuilder(),
    )
    trigger = IncidentTrigger(
        reason="BackOff",
        namespace="kubesage",
        pod="payment-api",
        message="Back-off restarting failed container",
        occurred_at=datetime.now(UTC),
    )
    watcher.handle(trigger)

    analysis_service.analyze.assert_called_once_with(
        "kubesage",
        "payment-api",
        AnalysisTrigger.WATCHER,
    )


def test_watcher_starts_analysis_for_incident() -> None:
    analysis_service = Mock()
    analysis_service.analyze.return_value = Mock(spec=Analysis)

    watcher = KubernetesWatcher(
        analysis_service=analysis_service,
        event_filter=PodEventFilter(),
        deduplicator=IncidentDeduplicator(),
        state_cache=PodStateCache(),
        diff_builder=PodStateDiffBuilder(),
    )
    event_source = FakeEventSource(build_event(build_pod("CrashLoopBackOff")))
    watcher.start(event_source)

    analysis_service.analyze.assert_called_once_with(
        "production",
        "payment-api",
        AnalysisTrigger.WATCHER,
    )


def test_duplicate_incident_is_ignored() -> None:
    analysis_service = Mock()
    analysis_service.analyze.return_value = Mock(spec=Analysis)

    watcher = KubernetesWatcher(
        analysis_service=analysis_service,
        event_filter=PodEventFilter(),
        deduplicator=IncidentDeduplicator(),
        state_cache=PodStateCache(),
        diff_builder=PodStateDiffBuilder(),
    )

    event_source = FakeEventSource(build_event(build_pod("CrashLoopBackOff")))

    watcher.start(event_source)
    watcher.start(event_source)

    assert True
