from datetime import UTC, datetime, timedelta

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


def correlated_but_not_causal_scenario() -> ReportQualityScenario:
    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="kubesage-correlated-noncausal",
    )

    incident = Incident(
        namespace="default",
        pod="kubesage-correlated-noncausal",
        phase="Running",
        observed_at=OBSERVED_AT,
    )

    cpu = Finding(
        rule="high_cpu_usage",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        confidence=0.9,
        title="CPU usage increased",
        description=(
            "CPU usage increased significantly shortly before an "
            "application error was observed."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="cpu_usage",
                value="92",
                unit="m",
                source="prometheus",
                type=EvidenceType.METRIC,
                description=(
                    "CPU usage increased to 92m shortly before the application error."
                ),
            ),
        ],
    )

    application_error = Finding(
        rule="application_error",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.HIGH,
        confidence=0.95,
        title="Application error detected",
        description=(
            "The application reported an internal error. The available "
            "evidence does not establish that CPU usage caused the error."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="application_error",
                value="HTTP 500",
                source="loki",
                type=EvidenceType.LOG,
                description=(
                    "Application logs report an HTTP 500 internal server error."
                ),
            ),
        ],
        recommendations=[
            "Investigate the application error and its underlying cause.",
            "Review application logs around the failure timestamp.",
        ],
    )

    restart = Finding(
        rule="container_restart",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        confidence=1.0,
        title="Container restarted",
        description=(
            "The container restarted after the application error, "
            "but no termination reason is available."
        ),
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
            id="cpu-increase",
            timestamp=OBSERVED_AT - timedelta(seconds=20),
            type=TimelineEventType.METRIC_ANOMALY,
            source=TimelineEventSource.PROMETHEUS,
            title="CPU usage increased",
            description="CPU usage reached 92m.",
            severity=Severity.WARNING,
            resource=resource,
        ),
        TimelineEvent(
            id="application-error",
            timestamp=OBSERVED_AT - timedelta(seconds=10),
            type=TimelineEventType.METRIC_CHANGE,
            source=TimelineEventSource.LOKI,
            title="Application error",
            description="Application returned HTTP 500.",
            severity=Severity.HIGH,
            resource=resource,
        ),
        TimelineEvent(
            id="container-restart",
            timestamp=OBSERVED_AT,
            type=TimelineEventType.CONTAINER_TERMINATED,
            source=TimelineEventSource.KUBERNETES,
            title="Container restarted",
            description="Container restarted after the application error.",
            severity=Severity.WARNING,
            resource=resource,
        ),
    ]

    return ReportQualityScenario(
        name="correlated_but_not_causal",
        incident=incident,
        findings=[cpu, application_error, restart],
        timeline=timeline,
        forbidden_root_cause_keywords=(
            "cpu caused",
            "cpu caused the error",
            "cpu throttling caused",
            "cpu exhaustion caused",
            "high cpu caused",
        ),
        required_evidence_keywords=("500", "cpu"),
        required_recommendation_keywords=("application", "logs"),
        require_root_cause=True,
        require_uncertainty=False,
    )
