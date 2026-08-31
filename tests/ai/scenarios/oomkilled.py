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

OBSERVED_AT = datetime(2026, 8, 31, 12, 0, 0, tzinfo=UTC)


def make_resource() -> ResourceRef:
    return ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="kubesage-oom",
    )


def make_oomkilled_observation() -> Finding:
    return Finding(
        rule="oom_killed",
        kind=FindingKind.OBSERVATION,
        severity=Severity.CRITICAL,
        confidence=1.0,
        title="Container OOMKilled",
        description=(
            "The container was terminated by Kubernetes with reason OOMKilled."
        ),
        resource=make_resource(),
        structured_evidences=[
            Evidence(
                name="termination_reason",
                value="OOMKilled",
                source="kubernetes",
                type=EvidenceType.CONTAINER_STATE,
                description=(
                    "The previous container state reports termination reason OOMKilled."
                ),
            )
        ],
    )


def make_high_memory_observation() -> Finding:
    return Finding(
        rule="high_memory_usage",
        kind=FindingKind.OBSERVATION,
        severity=Severity.HIGH,
        confidence=0.95,
        title="High memory usage",
        description=("Container memory consumption reached its configured limit."),
        resource=make_resource(),
        structured_evidences=[
            Evidence(
                name="memory_usage",
                value="64",
                unit="Mi",
                source="prometheus",
                type=EvidenceType.METRIC,
            ),
            Evidence(
                name="memory_limit",
                value="64",
                unit="Mi",
                source="kubernetes",
                type=EvidenceType.THRESHOLD,
            ),
        ],
    )


def make_memory_exhaustion_diagnosis() -> Finding:
    return Finding(
        rule="memory_exhaustion",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.CRITICAL,
        confidence=0.98,
        title="Memory exhaustion",
        description=(
            "The container reached its configured memory limit "
            "and was terminated with reason OOMKilled."
        ),
        resource=make_resource(),
        caused_by=[
            "high_memory_usage",
            "oom_killed",
        ],
        recommendations=[
            "Review the container memory limit and observed memory usage.",
            (
                "Investigate why the application requires more memory "
                "than the configured limit."
            ),
        ],
        structured_evidences=[
            Evidence(
                name="termination_reason",
                value="OOMKilled",
                source="kubernetes",
                type=EvidenceType.CONTAINER_STATE,
            ),
            Evidence(
                name="memory_limit",
                value="64",
                unit="Mi",
                source="kubernetes",
                type=EvidenceType.THRESHOLD,
            ),
        ],
    )


def make_timeline() -> list[TimelineEvent]:
    return [
        TimelineEvent(
            id="memory-limit-reached",
            timestamp=datetime(2026, 8, 31, 11, 59, 55, tzinfo=UTC),
            type=TimelineEventType.METRIC_ANOMALY,
            source=TimelineEventSource.PROMETHEUS,
            title="Memory usage reached container limit",
            description=("Container memory usage reached the configured 64Mi limit."),
            severity=Severity.HIGH,
            resource=make_resource(),
        ),
        TimelineEvent(
            id="container-oomkilled",
            timestamp=datetime(2026, 8, 31, 12, 0, 0, tzinfo=UTC),
            type=TimelineEventType.CONTAINER_TERMINATED,
            source=TimelineEventSource.KUBERNETES,
            title="Container terminated",
            description="Container 'stress' terminated: OOMKilled.",
            severity=Severity.CRITICAL,
            resource=make_resource(),
        ),
    ]


def oomkilled_scenario() -> ReportQualityScenario:
    incident = Incident(
        namespace="default",
        pod="kubesage-oom",
        phase="Running",
        observed_at=OBSERVED_AT,
    )

    return ReportQualityScenario(
        name="oomkilled",
        incident=incident,
        findings=[
            make_high_memory_observation(),
            make_oomkilled_observation(),
            make_memory_exhaustion_diagnosis(),
        ],
        timeline=make_timeline(),
        expected_root_cause_keywords=("memory", "oom"),
        forbidden_root_cause_keywords=("memory leak",),
        required_evidence_keywords=("OOMKilled", "memory", "64Mi"),
        required_recommendation_keywords=("memory",),
        require_root_cause=True,
    )
