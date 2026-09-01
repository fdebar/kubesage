from datetime import UTC, datetime

from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity
from kubesage.models.incident import Incident
from tests.ai.scenarios import ReportQualityScenario

OBSERVED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)


def correlated_oom_scenario() -> ReportQualityScenario:
    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="kubesage-correlated-oom",
    )

    incident = Incident(
        namespace="default",
        pod="kubesage-correlated-oom",
        phase="Running",
        observed_at=OBSERVED_AT,
    )

    high_memory = Finding(
        rule="high_memory_usage",
        kind=FindingKind.OBSERVATION,
        severity=Severity.HIGH,
        confidence=0.98,
        title="High memory usage",
        description="Memory usage reached the configured container limit.",
        resource=resource,
        structured_evidences=[],
    )

    oom = Finding(
        rule="oom_killed",
        kind=FindingKind.OBSERVATION,
        severity=Severity.CRITICAL,
        confidence=1.0,
        title="Container OOMKilled",
        description="The container was terminated with reason OOMKilled.",
        resource=resource,
        structured_evidences=[],
    )

    restart = Finding(
        rule="container_restart",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        confidence=1.0,
        title="Container restarted",
        description="The container restarted after termination.",
        resource=resource,
        structured_evidences=[
            Evidence(
                name="restart_count",
                value="5",
                source="kubernetes",
                type=EvidenceType.CONTAINER_STATE,
            ),
        ],
    )

    diagnosis = Finding(
        rule="memory_exhaustion",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.CRITICAL,
        confidence=0.99,
        title="Memory exhaustion",
        description=(
            "The container exceeded its memory limit, was OOMKilled, "
            "and subsequently restarted."
        ),
        resource=resource,
        caused_by=[
            "high_memory_usage",
            "oom_killed",
            "container_restart",
        ],
        recommendations=[
            "Review the configured memory limit.",
            "Investigate the application's memory consumption.",
        ],
        structured_evidences=[],
    )

    return ReportQualityScenario(
        name="correlated_oom",
        incident=incident,
        findings=[high_memory, oom, restart, diagnosis],
        expected_root_cause_keywords=("memory", "oom"),
        required_evidence_keywords=("memory", "OOMKilled"),
        required_recommendation_keywords=("memory",),
        require_root_cause=True,
    )
