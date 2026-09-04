from datetime import UTC, datetime

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
from kubesage.models.incident_intelligence import (
    IncidentIntelligence,
    RootCauseCandidate,
)
from kubesage.models.log import LogEntry, LogSnapshot
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
        events=[
            Event(
                type="Warning",
                reason="BackOff",
                message="Back-off restarting failed container",
                last_timestamp=datetime.fromisoformat("2023-01-01T00:00:00Z"),
            )
        ],
        kubernetes_logs=LogSnapshot(
            source="kubernetes",
            entries=[
                LogEntry(timestamp=datetime.now(), message="CrashLoopBackOff detected")
            ],
        ),
    )


def make_resource() -> ResourceRef:
    return ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="nginx-123",
    )


def make_diagnosis() -> IncidentIntelligence:
    return IncidentIntelligence(
        findings=[
            Finding(
                rule="high_cpu_usage",
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
        ],
        root_causes=[],
        correlations=[],
        timeline=[],
    )


def make_observation() -> IncidentIntelligence:
    return IncidentIntelligence(
        findings=[
            Finding(
                rule="restart_count",
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
        ],
        root_causes=[],
        correlations=[],
        timeline=[],
    )


def test_build_prompt_without_findings() -> None:
    builder = PromptBuilder()
    context = AIContext(
        make_incident(),
        IncidentIntelligence(findings=[], root_causes=[], correlations=[], timeline=[]),
    )

    prompt = builder.build(context)

    assert "# Kubernetes Incident" in prompt
    assert "Namespace: default" in prompt
    assert "Pod: nginx-123" in prompt
    assert "Phase: Running" in prompt

    assert "# Diagnostic Summary" not in prompt
    assert "# Diagnoses" not in prompt
    assert "# Observations" not in prompt

    assert "# Kubernetes Events" in prompt
    assert "BackOff" in prompt

    # assert "# Logs" in prompt
    # assert "CrashLoopBackOff detected" in prompt

    assert (
        "You are a Senior Kubernetes Site Reliability Engineer "
        "specialized in incident diagnosis."
    ) in prompt


def test_build_prompt_with_diagnosis() -> None:
    builder = PromptBuilder()

    intelligence = make_diagnosis()
    context = AIContext(make_incident(), intelligence)

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

    intelligence = make_observation()
    context = AIContext(make_incident(), intelligence)

    prompt = builder.build(context)

    assert "# Observations" in prompt
    assert "### Container restarted" in prompt
    assert "Description: Container restarted multiple times." in prompt

    assert "# Diagnoses" not in prompt


def test_build_prompt_with_multiple_findings() -> None:
    builder = PromptBuilder()

    intelligence = make_diagnosis()
    intelligence.findings.extend(make_observation().findings)
    context = AIContext(make_incident(), intelligence)

    prompt = builder.build(context)

    assert "# Diagnoses" in prompt
    assert "# Observations" in prompt
    assert "Count: 2" in prompt
    assert "### High CPU usage" in prompt
    assert "### Container restarted" in prompt


def test_root_causes_returns_top_level_diagnosis() -> None:
    intermediate = Finding(
        rule="memory_exhaustion",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.CRITICAL,
        title="Memory exhaustion",
        description="Memory exhausted",
        caused_by=[
            "high_memory_usage",
            "oom_killed",
        ],
    )

    root = Finding(
        rule="crash_loop_root_cause",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.CRITICAL,
        title="CrashLoop caused by memory exhaustion",
        description="CrashLoop is caused by memory exhaustion",
        caused_by=[
            "crashloop",
            "memory_exhaustion",
        ],
    )

    intermediate_root = RootCauseCandidate(
        finding="memory_exhaustion",
        title="Memory exhaustion",
        description="Memory exhausted",
        supporting_findings=["high_memory_usage", "oom_killed"],
        confidence=0.95,
    )

    context = AIContext(
        make_incident(),
        IncidentIntelligence(
            findings=[intermediate, root],
            root_causes=[intermediate_root],
            correlations=[],
            timeline=[],
        ),
    )

    assert len(context.root_causes) == 1
    assert context.root_causes[0] == intermediate_root


def test_root_causes_returns_all_independent_diagnoses() -> None:
    cpu = Finding(
        rule="cpu_contention",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.HIGH,
        title="CPU contention",
        description="CPU contention detected",
        caused_by=[
            "high_cpu_usage",
            "cpu_throttling",
        ],
    )
    memory = Finding(
        rule="memory_exhaustion",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.CRITICAL,
        title="Memory exhaustion",
        description="Memory exhaustion detected",
        caused_by=[
            "high_memory_usage",
            "oom_killed",
        ],
    )

    cpu_root = RootCauseCandidate(
        finding="cpu_contention",
        title="CPU contention",
        description="CPU contention detected",
        supporting_findings=["high_cpu_usage", "cpu_throttling"],
        confidence=0.8,
    )
    memory_root = RootCauseCandidate(
        finding="memory_exhaustion",
        title="Memory exhaustion",
        description="Memory exhaustion detected",
        supporting_findings=["high_memory_usage", "oom_killed"],
        confidence=0.8,
    )

    context = AIContext(
        make_incident(),
        IncidentIntelligence(
            findings=[cpu, memory],
            root_causes=[cpu_root, memory_root],
            correlations=[],
            timeline=[],
        ),
    )

    assert context.root_causes[0].supporting_findings == cpu.caused_by
    assert context.root_causes[1].supporting_findings == memory.caused_by


def test_root_causes_ignores_observations() -> None:
    observation = Finding(
        rule="oom_killed",
        kind=FindingKind.OBSERVATION,
        severity=Severity.HIGH,
        title="OOMKilled",
        description="Container was killed",
    )

    intelligence = IncidentIntelligence(
        findings=[observation],
        root_causes=[],
        correlations=[],
        timeline=[],
    )
    context = AIContext(make_incident(), intelligence)

    assert context.root_causes == []


def test_build_includes_timeline() -> None:
    observation = Finding(
        rule="oom_killed",
        kind=FindingKind.OBSERVATION,
        severity=Severity.HIGH,
        title="OOMKilled",
        description="Container was killed",
    )

    timeline = [
        TimelineEvent(
            id="container-terminated-api",
            timestamp=datetime(2026, 8, 31, 10, 42, 12, tzinfo=UTC),
            type=TimelineEventType.CONTAINER_TERMINATED,
            source=TimelineEventSource.KUBERNETES,
            title="Container terminated",
            description="Container 'api' terminated: OOMKilled.",
        )
    ]

    intelligence = IncidentIntelligence(
        findings=[observation],
        root_causes=[],
        correlations=[],
        timeline=timeline,
    )
    context = AIContext(make_incident(), intelligence)

    assert context.ctx.timeline == timeline
