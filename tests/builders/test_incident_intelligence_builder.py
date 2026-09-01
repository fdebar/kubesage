from datetime import datetime
from unittest.mock import Mock

from kubesage.builders.incident_intelligence_builder import (
    IncidentIntelligenceBuilder,
)
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity
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


def build_incident() -> Incident:
    return Incident(
        namespace="production",
        pod="payment-api",
        pod_uid="123e4567-e89b-12d3-a456-426614174000",
        phase="Running",
        observed_at=datetime.now(),
        containers=[],
        events=[],
        kubernetes_logs=None,
        loki_logs=None,
        prometheus=None,
        metrics=None,
    )


def test_builds_incident_intelligence() -> None:
    incident = build_incident()
    timeline_builder = Mock()

    timeline = [
        TimelineEvent(
            id="event-1",
            timestamp=incident.observed_at,
            type=TimelineEventType.KUBERNETES_EVENT,
            source=TimelineEventSource.KUBERNETES,
            title="Pod restarted",
        )
    ]
    timeline_builder.build.return_value = timeline
    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)
    finding = Finding(
        rule="crashloop",
        severity=Severity.HIGH,
        title="Container restarting",
        description="Container restarted repeatedly.",
    )
    result = builder.build(incident, [finding])

    assert isinstance(result, IncidentIntelligence)
    assert result.findings == [finding]
    assert result.timeline == timeline

    timeline_builder.build.assert_called_once_with(incident)


def test_build_with_no_findings() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)

    result = builder.build(incident, [])

    assert result.findings == []
    assert result.timeline == []
    assert result.correlations == []
    assert result.root_causes == []


def test_preserves_findings_order() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)

    finding_a = Finding(
        rule="rule_a",
        severity=Severity.WARNING,
        title="A",
        description="Finding A",
    )

    finding_b = Finding(
        rule="rule_b",
        severity=Severity.CRITICAL,
        title="B",
        description="Finding B",
    )

    result = builder.build(incident, [finding_a, finding_b])

    assert result.findings == [finding_a, finding_b]


def test_builds_correlations_from_caused_by() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(
        timeline_builder=timeline_builder,
    )

    diagnosis = Finding(
        rule="memory_exhaustion",
        severity=Severity.CRITICAL,
        title="Memory exhaustion",
        description="Memory exhaustion detected.",
        kind=FindingKind.DIAGNOSIS,
        caused_by=[
            "high_memory_usage",
            "oom_killed",
        ],
    )

    result = builder.build(
        incident,
        [diagnosis],
    )

    assert len(result.correlations) == 2

    assert result.correlations[0].source_finding == "memory_exhaustion"
    assert result.correlations[0].target_finding == "high_memory_usage"
    assert result.correlations[0].type == CorrelationType.CAUSED_BY

    assert result.correlations[1].source_finding == "memory_exhaustion"
    assert result.correlations[1].target_finding == "oom_killed"
    assert result.correlations[1].type == CorrelationType.CAUSED_BY


def test_builds_related_correlations() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)
    finding = Finding(
        rule="application_error",
        severity=Severity.ERROR,
        title="Application error",
        description="Application error detected.",
        related_findings=[
            "readiness_failure",
        ],
    )

    result = builder.build(incident, [finding])

    assert result.correlations == [
        Correlation(
            source_finding="application_error",
            target_finding="readiness_failure",
            type=CorrelationType.RELATED,
        )
    ]


def test_deduplicates_correlations() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)
    finding = Finding(
        rule="memory_exhaustion",
        severity=Severity.CRITICAL,
        title="Memory exhaustion",
        description="Memory exhaustion detected.",
        caused_by=[
            "oom_killed",
            "oom_killed",
        ],
    )

    result = builder.build(incident, [finding])

    assert len(result.correlations) == 1


def test_builds_root_cause_candidate_from_diagnosis() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder()
    diagnosis = Finding(
        rule="memory_exhaustion",
        severity=Severity.CRITICAL,
        title="Memory exhaustion",
        description="Memory exhaustion detected.",
        kind=FindingKind.DIAGNOSIS,
        caused_by=["high_memory_usage", "oom_killed"],
    )

    result = builder.build(incident, [diagnosis])

    assert len(result.root_causes) == 1

    candidate = result.root_causes[0]
    assert candidate.finding == "memory_exhaustion"
    assert candidate.title == "Memory exhaustion"
    assert candidate.description == "Memory exhaustion detected."
    assert candidate.confidence == 1.0
    assert candidate.supporting_findings == ["high_memory_usage", "oom_killed"]
    assert candidate.supporting_evidence == []


def test_observation_is_not_root_cause_candidate() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)
    finding = Finding(
        rule="high_memory_usage",
        severity=Severity.WARNING,
        title="High memory usage",
        description="High memory usage detected.",
        kind=FindingKind.OBSERVATION,
    )

    result = builder.build(incident, [finding])

    assert result.root_causes == []


def test_diagnosis_without_caused_by_is_not_root_cause() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)
    finding = Finding(
        rule="memory_exhaustion",
        severity=Severity.CRITICAL,
        title="Memory exhaustion",
        description="Memory exhaustion detected.",
        kind=FindingKind.DIAGNOSIS,
    )

    result = builder.build(incident, [finding])

    assert result.root_causes == []


def test_builds_multiple_root_cause_candidates() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)

    memory = Finding(
        rule="memory_exhaustion",
        severity=Severity.CRITICAL,
        title="Memory exhaustion",
        description="Memory exhaustion.",
        kind=FindingKind.DIAGNOSIS,
        caused_by=["oom_killed"],
    )

    cpu = Finding(
        rule="cpu_contention",
        severity=Severity.HIGH,
        title="CPU contention",
        description="CPU contention.",
        kind=FindingKind.DIAGNOSIS,
        caused_by=["cpu_throttling"],
    )

    result = builder.build(incident, [memory, cpu])

    assert len(result.root_causes) == 2
    assert result.root_causes[0].finding == "memory_exhaustion"
    assert result.root_causes[0].supporting_findings == ["oom_killed"]
    assert result.root_causes[1].finding == "cpu_contention"
    assert result.root_causes[1].supporting_findings == ["cpu_throttling"]


def test_root_cause_includes_supporting_evidence() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)

    memory_evidence = Evidence(
        name="container_memory_working_set_bytes",
        description="Container memory usage",
        source="prometheus",
        type=EvidenceType.METRIC,
        value="512Mi",
    )

    oom_evidence = Evidence(
        name="OOMKilled",
        description="Container was killed because of OOM",
        source="kubernetes",
        type=EvidenceType.EVENT,
    )

    memory = Finding(
        rule="high_memory_usage",
        severity=Severity.WARNING,
        title="High memory usage",
        description="Memory usage is high.",
        structured_evidences=[memory_evidence],
    )

    oom = Finding(
        rule="oom_killed",
        severity=Severity.CRITICAL,
        title="OOMKilled",
        description="Container was OOMKilled.",
        structured_evidences=[oom_evidence],
    )

    diagnosis = Finding(
        rule="memory_exhaustion",
        severity=Severity.CRITICAL,
        title="Memory exhaustion",
        description="Memory exhaustion detected.",
        kind=FindingKind.DIAGNOSIS,
        caused_by=["high_memory_usage", "oom_killed"],
    )

    result = builder.build(incident, [memory, oom, diagnosis])
    assert len(result.root_causes) == 1

    candidate = result.root_causes[0]
    assert candidate.finding == "memory_exhaustion"
    assert candidate.supporting_findings == ["high_memory_usage", "oom_killed"]
    assert candidate.supporting_evidence == [memory_evidence.id, oom_evidence.id]


def test_root_cause_ignores_missing_supporting_finding() -> None:
    incident = build_incident()
    timeline_builder = Mock()
    timeline_builder.build.return_value = []

    builder = IncidentIntelligenceBuilder(timeline_builder=timeline_builder)

    diagnosis = Finding(
        rule="memory_exhaustion",
        severity=Severity.CRITICAL,
        title="Memory exhaustion",
        description="Memory exhaustion detected.",
        kind=FindingKind.DIAGNOSIS,
        caused_by=[
            "high_memory_usage",
            "missing_finding",
        ],
    )

    memory = Finding(
        rule="high_memory_usage",
        severity=Severity.WARNING,
        title="High memory usage",
        description="Memory usage is high.",
    )

    result = builder.build(incident, [memory, diagnosis])
    candidate = result.root_causes[0]

    assert candidate.supporting_findings == ["high_memory_usage", "missing_finding"]
    assert candidate.supporting_evidence == []
