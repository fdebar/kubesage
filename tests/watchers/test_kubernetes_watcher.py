from datetime import UTC, datetime
from unittest.mock import Mock

from kubesage.models.analysis import Analysis
from kubesage.watchers.kubernetes_watcher import KubernetesWatcher
from kubesage.watchers.models import IncidentTrigger
from kubesage.watchers.pod_event_filter import PodEventFilter


def test_watcher_triggers_analysis() -> None:
    analysis_service = Mock()
    expected_analysis = Mock(spec=Analysis)
    analysis_service.analyze.return_value = expected_analysis

    watcher = KubernetesWatcher(
        analysis_service=analysis_service,
        event_filter=PodEventFilter(),
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
