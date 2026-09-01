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


def ambiguous_resource_pressure_scenario() -> ReportQualityScenario:
    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="kubesage-ambiguous-pressure",
    )

    incident = Incident(
        namespace="default",
        pod="kubesage-ambiguous-pressure",
        phase="Running",
        observed_at=OBSERVED_AT,
    )

    memory = Finding(
        rule="high_memory_usage",
        kind=FindingKind.OBSERVATION,
        severity=Severity.HIGH,
        confidence=0.85,
        title="High memory usage",
        description=(
            "Container memory usage increased significantly and remained "
            "close to its configured memory limit."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="memory_usage",
                value="58",
                unit="Mi",
                source="prometheus",
                type=EvidenceType.METRIC,
                description=(
                    "Container memory usage reached 58Mi while the configured "
                    "memory limit is 64Mi."
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

    cpu = Finding(
        rule="high_cpu_usage",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        confidence=0.8,
        title="High CPU usage",
        description=(
            "Container CPU usage increased significantly and approached "
            "its configured CPU limit."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="cpu_usage",
                value="95",
                unit="m",
                source="prometheus",
                type=EvidenceType.METRIC,
                description=(
                    "Container CPU usage reached 95m while the configured "
                    "CPU limit is 100m."
                ),
            ),
        ],
    )

    restart = Finding(
        rule="container_restart",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        confidence=1.0,
        title="Container restarted",
        description="The container restarted once during the incident window.",
        resource=resource,
        structured_evidences=[
            Evidence(
                name="restart_count",
                value="1",
                source="kubernetes",
                type=EvidenceType.CONTAINER_STATE,
                description="Container restart count increased to 1.",
            ),
        ],
    )

    timeline = [
        TimelineEvent(
            id="memory-pressure",
            timestamp=datetime(2026, 8, 31, 11, 59, 50, tzinfo=UTC),
            type=TimelineEventType.METRIC_ANOMALY,
            source=TimelineEventSource.PROMETHEUS,
            title="Memory usage increased",
            description="Memory usage reached 58Mi of a configured 64Mi limit.",
            severity=Severity.HIGH,
            resource=resource,
        ),
        TimelineEvent(
            id="cpu-pressure",
            timestamp=datetime(2026, 8, 31, 11, 59, 55, tzinfo=UTC),
            type=TimelineEventType.METRIC_ANOMALY,
            source=TimelineEventSource.PROMETHEUS,
            title="CPU usage increased",
            description="CPU usage reached 95m of a configured 100m limit.",
            severity=Severity.WARNING,
            resource=resource,
        ),
        TimelineEvent(
            id="container-restart",
            timestamp=OBSERVED_AT,
            type=TimelineEventType.CONTAINER_TERMINATED,
            source=TimelineEventSource.KUBERNETES,
            title="Container restarted",
            description="Container restarted once.",
            severity=Severity.WARNING,
            resource=resource,
        ),
    ]

    return ReportQualityScenario(
        name="ambiguous_resource_pressure",
        incident=incident,
        findings=[memory, cpu, restart],
        timeline=timeline,
        forbidden_root_cause_keywords=(
            "oomkilled",
            "oom killed",
            "out of memory",
            "memory leak",
            "memory usage reached the configured limit",
            "memory reached the configured limit",
            "resource exhaustion",
            "cpu throttling",
            "cpu exhaustion",
            "cpu limit exceeded",
        ),
        required_evidence_keywords=("memory", "cpu"),
        required_recommendation_keywords=("logs",),
        require_root_cause=False,
        require_uncertainty=True,
    )
