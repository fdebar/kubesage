from datetime import UTC, datetime

from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity
from kubesage.models.incident import Incident
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)
from tests.ai.scenarios import ReportQualityScenario

OBSERVED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)


def readiness_failure_scenario() -> ReportQualityScenario:
    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="kubesage-readiness",
    )

    incident = Incident(
        namespace="default",
        pod="kubesage-readiness",
        phase="Running",
        observed_at=OBSERVED_AT,
    )

    finding = Finding(
        rule="readiness_failure",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.WARNING,
        confidence=1.0,
        title="Readiness probe failing",
        description=(
            "The container is running but its readiness probe is failing, "
            "so the pod is not considered ready."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="probe_failure",
                value="HTTP 404",
                source="kubernetes",
                type=EvidenceType.EVENT,
            ),
            Evidence(
                name="container_state",
                value="Running",
                source="kubernetes",
                type=EvidenceType.CONTAINER_STATE,
            ),
        ],
        recommendations=[
            "Verify the readiness probe endpoint and configuration.",
            "Check that the application exposes the expected health endpoint.",
        ],
    )

    timeline = [
        TimelineEvent(
            id="readiness-failure",
            timestamp=OBSERVED_AT,
            type=TimelineEventType.KUBERNETES_EVENT,
            source=TimelineEventSource.KUBERNETES,
            title="Readiness probe failed",
            description="Readiness probe returned HTTP 404.",
            severity=Severity.WARNING,
            resource=resource,
        )
    ]

    return ReportQualityScenario(
        name="readiness_failure",
        incident=incident,
        findings=[finding],
        timeline=timeline,
        expected_root_cause_keywords=("404", "probe"),
        forbidden_root_cause_keywords=("crash", "crashloop", "oom", "out of memory"),
        required_evidence_keywords=("readiness", "probe"),
        required_recommendation_keywords=("probe",),
        require_root_cause=True,
    )
