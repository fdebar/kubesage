from datetime import UTC, datetime

from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity
from kubesage.models.incident import Incident
from kubesage.models.log import LogEntry, LogSnapshot
from tests.ai.scenarios import ReportQualityScenario

OBSERVED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)


def application_error_scenario() -> ReportQualityScenario:
    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="kubesage-error-logs",
    )

    incident = Incident(
        namespace="default",
        pod="kubesage-error-logs",
        phase="Running",
        observed_at=OBSERVED_AT,
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            entries=[
                LogEntry(
                    timestamp=OBSERVED_AT,
                    message="INFO Application started",
                ),
                LogEntry(
                    timestamp=OBSERVED_AT,
                    message="INFO Processing request",
                ),
                LogEntry(
                    timestamp=OBSERVED_AT,
                    message="ERROR Database connection refused",
                ),
                LogEntry(
                    timestamp=OBSERVED_AT,
                    message="Exception: timeout",
                ),
            ],
            collected_at=OBSERVED_AT,
        ),
    )

    finding = Finding(
        rule="application_error",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.HIGH,
        confidence=0.95,
        title="Application database connection failure",
        description=(
            "Application logs explicitly report that the database "
            "connection was refused."
        ),
        resource=resource,
        structured_evidences=[
            Evidence(
                name="application_error",
                value="Database connection refused",
                source="loki",
                type=EvidenceType.LOG,
            ),
            Evidence(
                name="exception",
                value="timeout",
                source="loki",
                type=EvidenceType.LOG,
            ),
        ],
        recommendations=[
            "Verify database availability and network connectivity.",
            "Check the application's database connection configuration.",
        ],
    )

    return ReportQualityScenario(
        name="application_error",
        incident=incident,
        findings=[finding],
        expected_root_cause_keywords=("database", "connection"),
        forbidden_root_cause_keywords=("oom", "out of memory", "cpu throttling"),
        required_evidence_keywords=("database", "connection refused"),
        required_recommendation_keywords=("database", "connection"),
        require_root_cause=True,
    )
