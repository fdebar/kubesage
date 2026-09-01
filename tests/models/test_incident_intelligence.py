from kubesage.models.finding import Finding, Severity
from kubesage.models.incident_intelligence import (
    Correlation,
    CorrelationType,
    IncidentIntelligence,
    RootCauseCandidate,
)


def test_empty_incident_intelligence() -> None:
    intelligence = IncidentIntelligence()

    assert intelligence.findings == []
    assert intelligence.timeline == []
    assert intelligence.correlations == []
    assert intelligence.root_causes == []
    assert intelligence.recommendations == []


def test_correlation() -> None:
    correlation = Correlation(
        source_finding="finding-1",
        target_finding="finding-2",
        confidence=0.85,
        evidence=["evidence-1"],
        type=CorrelationType.CAUSED_BY,
    )

    assert correlation.source_finding == "finding-1"
    assert correlation.target_finding == "finding-2"
    assert correlation.confidence == 0.85
    assert correlation.evidence == ["evidence-1"]
    assert correlation.type == CorrelationType.CAUSED_BY


def test_root_cause_candidate() -> None:
    candidate = RootCauseCandidate(
        title="CPU throttling",
        finding="cpu_throttling",
        description="The container is constrained by its CPU limit.",
        confidence=0.9,
        supporting_findings=["finding-1"],
        supporting_evidence=["evidence-1", "evidence-2"],
    )

    assert candidate.title == "CPU throttling"
    assert candidate.confidence == 0.9
    assert candidate.supporting_findings == ["finding-1"]
    assert candidate.supporting_evidence == [
        "evidence-1",
        "evidence-2",
    ]


def test_incident_intelligence_with_findings() -> None:
    finding = Finding(
        rule="cpu_throttling",
        severity=Severity.WARNING,
        title="CPU throttling detected",
        description="The container is being throttled.",
    )

    intelligence = IncidentIntelligence(
        findings=[finding],
        recommendations=["Increase CPU limit"],
    )

    assert len(intelligence.findings) == 1
    assert intelligence.findings[0].rule == "cpu_throttling"
    assert intelligence.recommendations == ["Increase CPU limit"]


def test_correlation_confidence_must_be_between_zero_and_one() -> None:
    from pydantic import ValidationError

    try:
        Correlation(
            source_finding="finding-1",
            target_finding="finding-2",
            confidence=1.5,
            type=CorrelationType.CAUSED_BY,
        )
    except ValidationError:
        return

    raise AssertionError("Expected ValidationError")


def test_root_cause_confidence_must_be_between_zero_and_one() -> None:
    from pydantic import ValidationError

    try:
        RootCauseCandidate(
            title="CPU throttling",
            description="CPU constrained",
            confidence=-0.1,
            finding="cpu_throttling",
        )
    except ValidationError:
        return

    raise AssertionError("Expected ValidationError")
