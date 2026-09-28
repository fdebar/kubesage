from datetime import UTC, datetime, timedelta

from _pytest.monkeypatch import MonkeyPatch

from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)
from kubesage.utils.config import settings


def test_high_volume_context_is_bounded_and_keeps_top_signals(
    monkeypatch: MonkeyPatch,
) -> None:
    max_findings = 8
    max_events = 12
    monkeypatch.setattr(settings, "ai_context_max_findings", max_findings)
    monkeypatch.setattr(settings, "ai_timeline_max_events", max_events)

    start = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
    incident = Incident(
        namespace="default",
        pod="payments-api",
        phase="Running",
        observed_at=start,
    )
    resource = ResourceRef(
        api_version="v1",
        kind="Pod",
        namespace="default",
        name="payments-api",
    )
    diagnosis = Finding(
        rule="oom_killed",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.CRITICAL,
        confidence=1.0,
        title="Container OOMKilled",
        description="The container was terminated with reason OOMKilled.",
        resource=resource,
        structured_evidences=[
            Evidence(
                name="termination_reason",
                value="OOMKilled",
                source="kubernetes",
                type=EvidenceType.CONTAINER_STATE,
                description="Kubernetes recorded an OOMKilled termination.",
            ),
        ],
    )
    low_priority_findings = [
        Finding(
            rule=f"unrelated_observation_{index}",
            kind=FindingKind.OBSERVATION,
            severity=Severity.INFO,
            confidence=0.9,
            title=f"Unrelated observation {index}",
            description=f"Low priority context noise {index}.",
        )
        for index in range(200)
    ]

    critical_event = TimelineEvent(
        id="oomkilled-critical",
        timestamp=start + timedelta(seconds=40),
        type=TimelineEventType.KUBERNETES_EVENT,
        source=TimelineEventSource.KUBERNETES,
        title="OOMKilled termination",
        description="Container terminated after reaching its memory limit.",
        severity=Severity.CRITICAL,
        resource=resource,
    )
    unrelated_events = [
        TimelineEvent(
            id=f"unrelated-event-{index}",
            timestamp=start + timedelta(seconds=index),
            type=TimelineEventType.KUBERNETES_EVENT,
            source=TimelineEventSource.KUBERNETES,
            title=f"Unrelated warning {index}",
            description=f"Unrelated warning detail {index}. " + ("noise " * 20),
            severity=Severity.WARNING,
        )
        for index in range(300)
    ]
    repeated_errors = [
        TimelineEvent(
            id=f"repeated-error-{index}",
            timestamp=start + timedelta(milliseconds=index * 100),
            type=TimelineEventType.LOG_EVENT,
            source=TimelineEventSource.LOKI,
            title="Telemetry export failed",
            description="Telemetry exporter timed out while sending a batch.",
            severity=Severity.ERROR,
            metadata={
                "error_kind": "timeout",
                "error_fingerprint": "telemetry-export-timeout",
            },
            resource=resource,
        )
        for index in range(100)
    ]
    intelligence = IncidentIntelligence(
        findings=[diagnosis, *low_priority_findings],
        timeline=[critical_event, *unrelated_events, *repeated_errors],
    )

    context = AIContext(incident, intelligence)
    prompt = PromptBuilder().build(context)
    empty_context_prompt = PromptBuilder().build(
        AIContext(incident, IncidentIntelligence())
    )

    assert len(intelligence.findings) == 201
    assert context.finding_count == max_findings
    assert context.ctx.findings[0].rule == "oom_killed"
    assert len(intelligence.timeline) == 401
    assert len(context.ctx.timeline) == max_events

    selected_titles = {event.title for event in context.ctx.timeline}
    assert "OOMKilled termination" in selected_titles
    assert any(event.metadata.get("aggregated") for event in context.ctx.timeline)
    assert "Unrelated observation 199" not in prompt
    assert "Unrelated warning 299" not in prompt
    assert "OOMKilled termination" in prompt

    # Each selected finding/event is bounded in count and the synthetic error
    # summary remains compact, so a large source timeline cannot expand the
    # rendered prompt linearly with all 401 input events.
    assert (
        len(prompt) <= len(empty_context_prompt) + max_findings * 500 + max_events * 400
    )
