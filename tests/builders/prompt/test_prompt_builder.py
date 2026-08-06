from datetime import UTC, datetime

from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.event import Event
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident


def make_incident() -> Incident:
    return Incident(
        namespace="default",
        pod="nginx-123",
        phase="Running",
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


def make_diagnosis_with_evidence() -> Finding:
    return Finding(
        rule="memory-pressure",
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
        recommendations=["Increase container memory limit"],
    )


def test_prompt_contains_structured_evidence() -> None:
    builder = PromptBuilder()

    context = AIContext(
        make_incident(),
        [make_diagnosis_with_evidence()],
    )

    prompt = builder.build(context)

    assert "Evidence:" in prompt
    assert "Type: metric" in prompt
    assert "Name: memory_usage" in prompt
    assert "Value: 512Mi" in prompt
    assert "Source: prometheus" in prompt


def test_prompt_contains_event_timestamp() -> None:
    builder = PromptBuilder()

    context = AIContext(make_incident_with_event(), [])

    prompt = builder.build(context)

    assert "# Kubernetes Events" in prompt
    assert "Reason: OOMKilled" in prompt
    assert "Timestamp:" in prompt
    assert "2026-08-06T12:30:00+00:00" in prompt


def test_prompt_contains_json_contract() -> None:
    builder = PromptBuilder()
    context = AIContext(make_incident(), [make_diagnosis_with_evidence()])
    prompt = builder.build(context)

    assert "Return JSON matching this schema:" in prompt
    assert '"summary": "..."' in prompt
    assert '"root_cause": "..."' in prompt
    assert '"confidence": 0.0' in prompt
    assert '"impact": "..."' in prompt


def test_prompt_contains_finding_confidence() -> None:
    builder = PromptBuilder()
    context = AIContext(make_incident(), [make_diagnosis_with_evidence()])
    prompt = builder.build(context)

    assert "Confidence: 0.95" in prompt


def test_prompt_contains_recommendations() -> None:
    builder = PromptBuilder()
    context = AIContext(make_incident(), [make_diagnosis_with_evidence()])
    prompt = builder.build(context)

    assert "# Recommendations" in prompt
    assert "- Increase container memory limit" in prompt


def test_prompt_builder_is_deterministic() -> None:
    incident = Incident(
        namespace="default",
        pod="test-pod",
        phase="Running",
        containers=[],
        events=[],
        kubernetes_logs=None,
        loki_logs=None,
        prometheus=None,
        metrics=None,
    )

    context = AIContext(incident=incident, findings=[])
    builder = PromptBuilder()

    prompt_1 = builder.build(context)
    prompt_2 = builder.build(context)

    assert prompt_1 == prompt_2
    assert "# Diagnostic Summary" not in prompt_1
