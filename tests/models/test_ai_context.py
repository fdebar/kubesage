from datetime import UTC, datetime, timedelta

from kubesage.models.ai_context import AIContext
from kubesage.models.finding import Finding, FindingKind, Severity
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.models.log import LogEntry, LogSnapshot
from kubesage.models.timeline import (
    TimelineEvent,
    TimelineEventSource,
    TimelineEventType,
)


def make_event(
    event_id: str,
    *,
    offset_seconds: int = 0,
    severity: Severity = Severity.INFO,
    title: str = "Routine log",
    event_type: TimelineEventType = TimelineEventType.LOG_EVENT,
) -> TimelineEvent:
    return TimelineEvent(
        id=event_id,
        timestamp=datetime(2026, 9, 4, 10, 0, 0, tzinfo=UTC)
        + timedelta(seconds=offset_seconds),
        type=event_type,
        source=TimelineEventSource.LOKI,
        title=title,
        severity=severity,
    )


def make_incident() -> Incident:
    return Incident(
        namespace="monitoring",
        pod="monitoring-grafana",
        phase="Running",
        observed_at=datetime.now(),
        loki_logs=LogSnapshot(
            source="loki",
            entries=[LogEntry(timestamp=datetime.now(), message="full raw logs")],
        ),
    )


def make_finding() -> Finding:
    return Finding(
        rule="application_error",
        title="Database connection failure",
        kind=FindingKind.DIAGNOSIS,
        severity=Severity.ERROR,
        confidence=0.95,
        description="Database connection failed.",
    )


def test_ai_context_uses_selected_timeline() -> None:
    timeline = [
        make_event("info-1", title="Routine log", offset_seconds=-60),
        make_event(
            "error-1",
            severity=Severity.ERROR,
            title="Database connection failure",
            offset_seconds=0,
        ),
    ]

    intelligence = IncidentIntelligence(
        findings=[make_finding()],
        timeline=timeline,
        root_causes=[],
        correlations=[],
    )

    context = AIContext(make_incident(), intelligence)
    selected_ids = {event.id for event in context.ctx.timeline}

    assert "error-1" in selected_ids
    assert "info-1" not in selected_ids


def test_ai_context_does_not_modify_incident_intelligence_timeline() -> None:
    intelligence = IncidentIntelligence(
        findings=[make_finding()],
        timeline=[
            make_event("info-1", title="Routine log", offset_seconds=-60),
            make_event(
                "error-1",
                severity=Severity.ERROR,
                title="Database failure",
                offset_seconds=0,
            ),
        ],
        root_causes=[],
        correlations=[],
    )

    AIContext(make_incident(), intelligence)

    assert len(intelligence.timeline) == 2
    assert {event.id for event in intelligence.timeline} == {"info-1", "error-1"}


def test_ai_context_keeps_findings_ranked() -> None:
    finding = make_finding()
    context = AIContext(
        make_incident(),
        IncidentIntelligence(
            findings=[finding],
            timeline=[],
            root_causes=[],
            correlations=[],
        ),
    )

    assert context.ctx.findings == [finding]
