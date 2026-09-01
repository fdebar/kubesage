from datetime import UTC, datetime

from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.event import Event
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import (
    Correlation,
    CorrelationType,
    IncidentIntelligence,
)
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)


def make_incident() -> Incident:
    return Incident(
        namespace="default",
        pod="nginx-123",
        phase="Running",
        observed_at=datetime.now(),
        containers=[],
        events=[],
        prometheus=None,
        metrics=None,
    )


def make_incident_with_event() -> Incident:
    return Incident(
        namespace="default",
        pod="nginx-123",
        phase="Running",
        containers=[],
        observed_at=datetime.now(),
        events=[
            Event(
                type="Warning",
                reason="OOMKilled",
                message="Container nginx was killed due to memory limit",
                last_timestamp=datetime(2026, 8, 6, 12, 30, tzinfo=UTC),
            )
        ],
        prometheus=None,
        metrics=None,
    )


def make_diagnosis_with_evidence() -> IncidentIntelligence:
    return IncidentIntelligence(
        findings=[
            Finding(
                rule="memory_pressure",
                kind=FindingKind.DIAGNOSIS,
                severity=Severity.HIGH,
                title="Container memory limit exceeded",
                description="Container reached its configured memory limit.",
                confidence=0.95,
                structured_evidences=[
                    Evidence(
                        name="memory_usage",
                        value="512",
                        unit="Mi",
                        source="prometheus",
                        type=EvidenceType.METRIC,
                        description=(
                            "Container memory usage reached its configured limit."
                        ),
                    )
                ],
                recommendations=["Increase container memory limit"],
            )
        ],
        root_causes=[],
        correlations=[],
        timeline=[],
    )


def test_prompt_contains_structured_evidence() -> None:
    builder = PromptBuilder()
    incident = make_incident()
    intelligence = make_diagnosis_with_evidence()

    context = AIContext(incident=incident, intelligence=intelligence)
    prompt = builder.build(context)

    assert "Evidence:" in prompt
    assert "Type: metric" in prompt
    assert "Name: memory_usage" in prompt
    assert "Value: 512Mi" in prompt
    assert "Source: prometheus" in prompt
    assert "Description: Container memory usage reached its configured limit." in prompt


def test_prompt_contains_event_timestamp() -> None:
    builder = PromptBuilder()
    incident = make_incident_with_event()
    intelligence = make_diagnosis_with_evidence()
    context = AIContext(incident, intelligence)

    prompt = builder.build(context)

    assert "# Kubernetes Events" in prompt
    assert "Reason: OOMKilled" in prompt
    assert "Timestamp:" in prompt
    assert "2026-08-06T12:30:00+00:00" in prompt


def test_prompt_contains_json_contract() -> None:
    builder = PromptBuilder()
    incident = make_incident()
    intelligence = make_diagnosis_with_evidence()
    context = AIContext(incident, intelligence)
    prompt = builder.build(context)

    assert "Return JSON matching this schema:" in prompt
    assert '"summary": "..."' in prompt
    assert '"root_cause": "..."' in prompt
    assert '"confidence": 0.0' in prompt
    assert '"impact": "..."' in prompt


def test_prompt_contains_finding_confidence() -> None:
    builder = PromptBuilder()
    incident = make_incident()
    intelligence = make_diagnosis_with_evidence()
    context = AIContext(incident, intelligence)
    prompt = builder.build(context)

    assert "Confidence: 0.95" in prompt


def test_prompt_contains_recommendations() -> None:
    builder = PromptBuilder()
    incident = make_incident()
    intelligence = make_diagnosis_with_evidence()
    context = AIContext(incident, intelligence)
    prompt = builder.build(context)

    assert "# Recommendations" in prompt
    assert "- Increase container memory limit" in prompt


def test_prompt_builder_is_deterministic() -> None:
    intelligence = IncidentIntelligence(
        findings=[],
        root_causes=[],
        correlations=[],
        timeline=[],
    )
    incident = Incident(
        namespace="default",
        pod="test-pod",
        phase="Running",
        observed_at=datetime.now(),
        containers=[],
        events=[],
        kubernetes_logs=None,
        loki_logs=None,
        prometheus=None,
        metrics=None,
    )
    context = AIContext(incident, intelligence)
    builder = PromptBuilder()

    prompt_1 = builder.build(context)
    prompt_2 = builder.build(context)

    assert prompt_1 == prompt_2
    assert "# Diagnostic Summary" not in prompt_1


def test_prompt_omits_missing_evidence_description() -> None:
    finding = Finding(
        rule="memory_pressure",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.HIGH,
        title="Container memory limit exceeded",
        description="Container reached its configured memory limit.",
        confidence=0.95,
        structured_evidences=[
            Evidence(
                name="memory_usage",
                value="512",
                unit="Mi",
                source="prometheus",
                type=EvidenceType.METRIC,
            )
        ],
    )
    incident = make_incident()
    intelligence = IncidentIntelligence(findings=[finding])
    context = AIContext(incident, intelligence)
    prompt = PromptBuilder().build(context)

    evidence_section = prompt.split("Evidence:", maxsplit=1)[1]
    assert "Description:" not in evidence_section


def test_build_includes_incident_timeline() -> None:
    finding = Finding(
        rule="memory_pressure",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.HIGH,
        title="Container memory limit exceeded",
        description="Container reached its configured memory limit.",
        confidence=0.95,
        structured_evidences=[
            Evidence(
                name="memory_usage",
                value="512",
                unit="Mi",
                source="prometheus",
                type=EvidenceType.METRIC,
            )
        ],
    )

    timeline = [
        TimelineEvent(
            id="event-1",
            timestamp=datetime(2026, 8, 31, 10, 42, 12, tzinfo=UTC),
            type=TimelineEventType.CONTAINER_TERMINATED,
            source=TimelineEventSource.KUBERNETES,
            title="Container terminated",
            description="Container 'api' terminated: OOMKilled.",
        ),
        TimelineEvent(
            id="event-2",
            timestamp=datetime(2026, 9, 1, 10, 42, 12, tzinfo=UTC),
            type=TimelineEventType.METRIC_ANOMALY,
            source=TimelineEventSource.LOKI,
            title="Application error",
            description="Error: Memory allocation failed",
        ),
    ]
    incident = make_incident()
    intelligence = IncidentIntelligence(findings=[finding], timeline=timeline)
    context = AIContext(incident, intelligence)
    prompt = PromptBuilder().build(context)

    assert "# Incident Timeline" in prompt
    assert "[2026-08-31T10:42:12+00:00]" in prompt
    assert "[INFO] kubernetes | Container terminated" in prompt
    assert "Container 'api' terminated: OOMKilled." in prompt

    first = prompt.index("Container terminated")
    second = prompt.index("Application error")
    assert first < second


def test_prompt_contains_timeline_reasoning_instructions() -> None:
    finding = Finding(
        rule="memory_pressure",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.HIGH,
        title="Container memory limit exceeded",
        description="Container reached its configured memory limit.",
        confidence=0.95,
        structured_evidences=[
            Evidence(
                name="memory_usage",
                value="512",
                unit="Mi",
                source="prometheus",
                type=EvidenceType.METRIC,
            )
        ],
    )

    timeline = [
        TimelineEvent(
            id="event-1",
            timestamp=datetime(2026, 8, 31, 10, 42, 12, tzinfo=UTC),
            type=TimelineEventType.CONTAINER_TERMINATED,
            source=TimelineEventSource.KUBERNETES,
            title="Container terminated",
            description="Container 'api' terminated: OOMKilled.",
        ),
        TimelineEvent(
            id="event-2",
            timestamp=datetime(2026, 9, 1, 10, 42, 12, tzinfo=UTC),
            type=TimelineEventType.METRIC_ANOMALY,
            source=TimelineEventSource.LOKI,
            title="Application error",
            description="Error: Memory allocation failed",
        ),
    ]
    incident = make_incident()
    intelligence = IncidentIntelligence(findings=[finding], timeline=timeline)
    context = AIContext(incident, intelligence)
    prompt = PromptBuilder().build(context)

    assert "## Timeline reasoning" in prompt
    assert "temporal sequence of events" in prompt
    assert "Temporal proximity alone does not prove causality." in prompt


def test_build_includes_application_error_classification() -> None:
    finding = Finding(
        rule="application_error",
        severity=Severity.ERROR,
        kind=FindingKind.OBSERVATION,
        title="Database connection failure",
        description="Application logs report a database error.",
        metadata={
            "error_kind": "connection_error",
            "error_domain": "database",
        },
        confidence=0.90,
        priority=30,
        resource=ResourceRef(
            api_version="v1",
            kind="Pod",
            namespace="default",
            name="my-api",
        ),
        structured_evidences=[
            Evidence(
                type=EvidenceType.LOG,
                name="application_error",
                value="ERROR database connection refused",
                source="loki",
                description="Application error detected in Loki logs.",
            )
        ],
    )
    incident = make_incident()
    intelligence = IncidentIntelligence(findings=[finding])
    context = AIContext(incident, intelligence)
    prompt = PromptBuilder().build(context)

    assert "Classification:" in prompt
    assert "- Kind: connection_error" in prompt
    assert "- Domain: database" in prompt


def test_build_includes_error_kind_without_domain() -> None:
    finding = Finding(
        rule="application_error",
        severity=Severity.ERROR,
        kind=FindingKind.OBSERVATION,
        title="Application timeout",
        description="Application logs report a timeout.",
        metadata={
            "error_kind": "timeout",
            "error_domain": None,
        },
        confidence=0.90,
        priority=30,
        resource=ResourceRef(
            api_version="v1",
            kind="Pod",
            namespace="default",
            name="my-api",
        ),
    )
    incident = make_incident()
    intelligence = IncidentIntelligence(findings=[finding])
    context = AIContext(incident, intelligence)
    prompt = PromptBuilder().build(context)

    assert "Classification:" in prompt
    assert "- Kind: timeout" in prompt
    assert "- Domain:" not in prompt
    assert (
        "Distinguish clearly between observed facts and inferred conclusions." in prompt
    )
    assert "Do not assume that temporal proximity implies causality." in prompt
    assert "Do not invent missing technical details" in prompt
    assert "Confidence should reflect the strength of the available evidence." in prompt


def test_prompt_includes_correlations() -> None:
    correlation = Correlation(
        source_finding="memory_exhaustion",
        target_finding="high_memory_usage",
        type=CorrelationType.CAUSED_BY,
        confidence=0.9,
        evidence=["Evidence details"],
    )

    incident = make_incident()
    intelligence = IncidentIntelligence(correlations=[correlation])
    context = AIContext(incident, intelligence)
    prompt = PromptBuilder().build(context)

    assert "# Finding Correlations" in prompt
    assert "memory_exhaustion" in prompt
    assert "high_memory_usage" in prompt
    assert "[caused_by]" in prompt
    assert "Confidence: 0.90" in prompt


def test_prompt_with_empty_intelligence() -> None:
    incident = make_incident()
    intelligence = IncidentIntelligence()
    context = AIContext(incident, intelligence)
    prompt = PromptBuilder().build(context)

    assert "# Kubernetes Incident" in prompt
    assert "Namespace: default" in prompt
    assert "Pod: nginx-123" in prompt
    assert "Phase: Running" in prompt

    assert "# Incident Timeline" not in prompt
    assert "# Finding Correlations" not in prompt
    assert "# Root Cause Analysis" not in prompt
