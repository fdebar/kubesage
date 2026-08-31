from datetime import UTC, datetime

from kubesage.models.event import Event
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import (
    Finding,
    FindingKind,
    ResourceRef,
    Severity,
)
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry, LogSnapshot
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)
from tests.ai.scenarios import ReportQualityScenario

OBSERVED_AT = datetime(2026, 8, 31, 12, 0, 0, tzinfo=UTC)


def crashloop_unknown_scenario() -> ReportQualityScenario:
    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="kubesage-crashloop",
    )

    incident = Incident(
        namespace="default",
        pod="kubesage-crashloop",
        phase="Running",
        observed_at=OBSERVED_AT,
        events=[
            Event(
                type="Warning",
                reason="BackOff",
                message="Back-off restarting failed container app",
                last_timestamp=OBSERVED_AT,
            ),
        ],
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            entries=[
                LogEntry(
                    timestamp=OBSERVED_AT,
                    message="Application started",
                ),
                LogEntry(
                    timestamp=OBSERVED_AT,
                    message="Application exited unexpectedly",
                ),
            ],
            collected_at=OBSERVED_AT,
        ),
    )

    finding = Finding(
        rule="crashloop",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        confidence=1.0,
        title="Container restarting repeatedly",
        description=(
            "The container is repeatedly restarting and Kubernetes "
            "is applying a back-off."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="restart_backoff",
                value="BackOff",
                source="kubernetes",
                type=EvidenceType.EVENT,
            ),
        ],
    )

    timeline = [
        TimelineEvent(
            id="crashloop-backoff",
            timestamp=OBSERVED_AT,
            type=TimelineEventType.KUBERNETES_EVENT,
            source=TimelineEventSource.KUBERNETES,
            title="Container restart back-off",
            description="Back-off restarting failed container app.",
            severity=Severity.WARNING,
            resource=resource,
        ),
    ]

    return ReportQualityScenario(
        name="crashloop_unknown",
        incident=incident,
        findings=[finding],
        timeline=timeline,
        forbidden_root_cause_keywords=(
            "oom",
            "out of memory",
            "memory leak",
            "cpu throttling",
        ),
        require_root_cause=False,
        require_uncertainty=True,
    )
