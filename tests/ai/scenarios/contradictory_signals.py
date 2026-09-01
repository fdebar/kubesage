from datetime import UTC, datetime

from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import (
    Finding,
    FindingKind,
    ResourceRef,
    Severity,
)
from kubesage.models.incident import Incident
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)
from tests.ai.scenarios import ReportQualityScenario

OBSERVED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)


def contradictory_signals_scenario() -> ReportQualityScenario:
    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="kubesage-contradictory",
    )

    incident = Incident(
        namespace="default",
        pod="kubesage-contradictory",
        phase="Running",
        observed_at=OBSERVED_AT,
    )

    memory_observation = Finding(
        rule="memory_pressure",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        confidence=0.7,
        title="Memory pressure suspected",
        description=(
            "A diagnostic signal suggests possible memory pressure, "
            "but the available memory metric remains below the configured limit."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="memory_usage",
                value="48",
                unit="Mi",
                source="prometheus",
                type=EvidenceType.METRIC,
                description=(
                    "Container memory usage is 48Mi, below the configured "
                    "memory limit of 64Mi."
                ),
            ),
            Evidence(
                name="memory_limit",
                value="64",
                unit="Mi",
                source="kubernetes",
                type=EvidenceType.THRESHOLD,
                description="Container memory limit is configured to 64Mi.",
            ),
        ],
    )

    container_state = Finding(
        rule="container_running",
        kind=FindingKind.OBSERVATION,
        severity=Severity.INFO,
        confidence=1.0,
        title="Container remains running",
        description=(
            "The container is currently running and no termination reason "
            "such as OOMKilled is present."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="container_state",
                value="Running",
                source="kubernetes",
                type=EvidenceType.CONTAINER_STATE,
                description="The container is currently in the Running state.",
            ),
        ],
    )

    event = Finding(
        rule="container_restart",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        confidence=1.0,
        title="Container restart observed",
        description=(
            "The container restarted once, but no termination reason is available."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="restart_count",
                value="1",
                source="kubernetes",
                type=EvidenceType.CONTAINER_STATE,
                description="Container restart count is 1.",
            ),
        ],
    )

    timeline = [
        TimelineEvent(
            id="memory-observation",
            timestamp=datetime(2026, 8, 31, 11, 59, 50, tzinfo=UTC),
            type=TimelineEventType.METRIC_ANOMALY,
            source=TimelineEventSource.PROMETHEUS,
            title="Memory usage observed",
            description="Memory usage is 48Mi of a 64Mi limit.",
            severity=Severity.WARNING,
            resource=resource,
        ),
        TimelineEvent(
            id="container-restart",
            timestamp=OBSERVED_AT,
            type=TimelineEventType.CONTAINER_TERMINATED,
            source=TimelineEventSource.KUBERNETES,
            title="Container restarted",
            description=(
                "Container restarted, but no termination reason is available."
            ),
            severity=Severity.WARNING,
            resource=resource,
        ),
    ]

    return ReportQualityScenario(
        name="contradictory_signals",
        incident=incident,
        findings=[
            memory_observation,
            container_state,
            event,
        ],
        timeline=timeline,
        forbidden_root_cause_keywords=(
            "oomkilled",
            "oom killed",
            "out of memory",
            "memory limit exceeded",
            "memory exhaustion",
        ),
        required_evidence_keywords=("memory", "64Mi"),
        required_recommendation_keywords=("__investigation__",),
        require_root_cause=False,
        require_uncertainty=True,
    )
