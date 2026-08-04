from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import Mock

from kubesage.models.analysis import Analysis
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.kubernetes_watcher import KubernetesWatcher
from kubesage.watchers.models import IncidentTrigger, PodWatchEvent
from kubesage.watchers.pod_event_filter import PodEventFilter
from tests.watchers.test_pod_event_filter import build_event, build_pod


class FakeEventSource:
    def __init__(self, event: PodWatchEvent) -> None:
        self.event = event

    def watch(self) -> Iterator[PodWatchEvent]:
        yield self.event


def test_watcher_triggers_analysis() -> None:
    analysis_service = Mock()
    expected_analysis = Mock(spec=Analysis)
    analysis_service.analyze.return_value = expected_analysis

    watcher = KubernetesWatcher(
        analysis_service=analysis_service,
        event_filter=PodEventFilter(),
        deduplicator=IncidentDeduplicator(),
    )

    trigger = IncidentTrigger(
        reason="BackOff",
        namespace="kubesage",
        pod="payment-api",
        message="Back-off restarting failed container",
        occurred_at=datetime.now(UTC),
    )

    result = watcher.handle(trigger)

    assert result == expected_analysis

    analysis_service.analyze.assert_called_once_with(
        namespace="kubesage",
        pod="payment-api",
    )


def test_watcher_starts_analysis_for_incident() -> None:
    analysis_service = Mock()
    analysis_service.analyze.return_value = Mock(spec=Analysis)

    watcher = KubernetesWatcher(
        analysis_service=analysis_service,
        event_filter=PodEventFilter(),
        deduplicator=IncidentDeduplicator(),
    )
    event_source = FakeEventSource(build_event(build_pod("CrashLoopBackOff")))
    watcher.start(event_source)

    analysis_service.analyze.assert_called_once_with(
        namespace="production",
        pod="payment-api",
    )
