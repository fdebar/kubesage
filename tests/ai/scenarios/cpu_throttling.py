from datetime import UTC, datetime

from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity
from kubesage.models.incident import Incident
from tests.ai.scenarios import ReportQualityScenario

OBSERVED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)


def cpu_throttling_scenario() -> ReportQualityScenario:
    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="kubesage-cpu-throttling",
    )

    incident = Incident(
        namespace="default",
        pod="kubesage-cpu-throttling",
        phase="Running",
        observed_at=OBSERVED_AT,
    )

    finding = Finding(
        rule="cpu_throttling",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.WARNING,
        confidence=0.95,
        title="CPU throttling detected",
        description=(
            "The container is experiencing significant CPU throttling "
            "relative to its configured CPU limit."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="cpu_throttling_ratio",
                value="0.82",
                source="prometheus",
                type=EvidenceType.METRIC,
            ),
            Evidence(
                name="cpu_limit",
                value="100m",
                source="kubernetes",
                type=EvidenceType.THRESHOLD,
            ),
        ],
        recommendations=[
            "Review the configured CPU limit.",
            "Investigate whether the workload requires additional CPU capacity.",
        ],
    )

    return ReportQualityScenario(
        name="cpu_throttling",
        incident=incident,
        findings=[finding],
        timeline=[],
        expected_root_cause_keywords=("cpu", "thrott"),
        forbidden_root_cause_keywords=("oom", "out of memory", "crash"),
        required_evidence_keywords=("thrott", "cpu"),
        required_recommendation_keywords=("cpu",),
        require_root_cause=True,
    )
