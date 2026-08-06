from datetime import datetime

from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.event import Event
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import (
    Finding,
    FindingKind,
    ResourceRef,
    Severity,
)
from kubesage.models.incident import Incident
from kubesage.models.log import LogSnapshot


def make_incident() -> Incident:
    return Incident(
        namespace="default",
        pod="nginx-123",
        phase="Running",
        events=[
            Event(
                type="Warning",
                reason="BackOff",
                message="Back-off restarting failed container",
                last_timestamp=datetime.fromisoformat("2023-01-01T00:00:00Z"),
            )
        ],
        kubernetes_logs=LogSnapshot(
            lines=["CrashLoopBackOff detected"], source="kubernetes"
        ),
    )


def make_resource() -> ResourceRef:
    return ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="nginx-123",
    )


def make_diagnosis() -> Finding:
    return Finding(
        rule="HighCPUUsageRule",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.CRITICAL,
        confidence=0.95,
        title="High CPU usage",
        description="Container is CPU saturated.",
        recommendations=["Increase CPU limit"],
        structured_evidences=[
            Evidence(
                name="cpu_usage",
                value="95",
                unit="%",
                source="prometheus",
                type=EvidenceType.METRIC,
            )
        ],
        resource=make_resource(),
        caused_by=["cpu_throttling"],
    )


def make_observation() -> Finding:
    return Finding(
        rule="RestartRule",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        confidence=0.80,
        title="Container restarted",
        description="Container restarted multiple times.",
        recommendations=[],
        structured_evidences=[],
        resource=make_resource(),
        caused_by=[],
    )


def test_build_prompt_without_findings() -> None:
    builder = PromptBuilder()

    context = AIContext(make_incident(), [])

    prompt = builder.build(context)

    assert "# Kubernetes Incident" in prompt
    assert "Namespace: default" in prompt
    assert "Pod: nginx-123" in prompt
    assert "Phase: Running" in prompt

    assert "# Diagnostic Summary" not in prompt
    assert "# Diagnoses" not in prompt
    assert "# Observations" not in prompt
    assert "# Recommendations" not in prompt

    assert "# Kubernetes Events" in prompt
    assert "BackOff" in prompt

    assert "# Logs" in prompt
    assert "CrashLoopBackOff detected" in prompt

    assert "You are a Senior Kubernetes Site Reliability Engineer." in prompt


def test_build_prompt_with_diagnosis() -> None:
    builder = PromptBuilder()

    context = AIContext(make_incident(), [make_diagnosis()])

    prompt = builder.build(context)

    assert "# Diagnostic Summary" in prompt
    assert "Count: 1" in prompt
    assert f"Highest Severity: {Severity.CRITICAL.value.upper()}" in prompt

    assert "# Diagnoses" in prompt
    assert "### High CPU usage" in prompt
    assert f"Severity: {Severity.CRITICAL.value}" in prompt
    assert "Confidence: 0.95" in prompt
    assert "Description: Container is CPU saturated." in prompt

    assert "Caused by:" in prompt
    assert "cpu_throttling" in prompt

    assert "Evidence:" in prompt
    assert "Name: cpu_usage" in prompt
    assert "Value: 95%" in prompt

    assert "# Recommendations" in prompt
    assert "- Increase CPU limit" in prompt


def test_build_prompt_with_observation() -> None:
    builder = PromptBuilder()

    context = AIContext(make_incident(), [make_observation()])

    prompt = builder.build(context)

    assert "# Observations" in prompt
    assert "### Container restarted" in prompt
    assert "Description: Container restarted multiple times." in prompt

    assert "# Diagnoses" not in prompt
    assert "# Recommendations" not in prompt


def test_build_prompt_with_multiple_findings() -> None:
    builder = PromptBuilder()

    context = AIContext(
        make_incident(),
        [
            make_diagnosis(),
            make_observation(),
        ],
    )

    prompt = builder.build(context)

    assert "# Diagnoses" in prompt
    assert "# Observations" in prompt
    assert "Count: 2" in prompt
    assert "### High CPU usage" in prompt
    assert "### Container restarted" in prompt
