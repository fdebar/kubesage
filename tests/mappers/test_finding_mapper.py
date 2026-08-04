import pytest

from kubesage.mappers.finding_mapper import FindingMapper
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, Severity


@pytest.fixture
def finding() -> Finding:
    return Finding(
        rule="crash_loop",
        kind=FindingKind.OBSERVATION,
        severity=Severity.HIGH,
        title="Container restarting",
        description="Container restarted multiple times",
        recommendations=[
            "Check container logs",
            "Review resource limits",
        ],
        structured_evidences=[
            Evidence(
                name="restart_count",
                value="10",
                source="kubernetes",
                type=EvidenceType.METRIC,
                unit="count",
                metadata={
                    "container": "api",
                },
            )
        ],
    )


def test_to_model_creates_complete_model(finding: Finding) -> None:
    model = FindingMapper.to_model(finding, analysis_id="analysis-123")

    assert model.analysis_id == "analysis-123"
    assert model.rule == "crash_loop"
    assert model.kind == FindingKind.OBSERVATION
    assert model.severity == Severity.HIGH

    assert model.title == "Container restarting"
    assert model.description == "Container restarted multiple times"

    assert len(model.evidences) == 1
    assert model.evidences[0].name == "restart_count"
    assert model.evidences[0].value == "10"
    assert model.evidences[0].source == "kubernetes"
    assert model.evidences[0].type == "metric"

    assert len(model.recommendations) == 2
    assert model.recommendations[0].text == "Check container logs"


def test_to_model_without_optional_data() -> None:
    finding = Finding(
        rule="pending",
        kind=FindingKind.OBSERVATION,
        severity=Severity.WARNING,
        title="Pod pending",
        description="Pod cannot be scheduled",
    )
    model = FindingMapper.to_model(finding, analysis_id="123")

    assert model.evidences == []
    assert model.recommendations == []


def test_to_model_preserves_evidence_metadata(
    finding: Finding,
) -> None:
    model = FindingMapper.to_model(finding, analysis_id="123")
    evidence = model.evidences[0]

    assert evidence.evidence_metadata == {"container": "api"}


def test_to_domain_restores_finding(finding: Finding) -> None:
    model = FindingMapper.to_model(finding, analysis_id="123")
    domain = FindingMapper.to_domain(model)

    assert domain.rule == finding.rule
    assert domain.kind == FindingKind.OBSERVATION
    assert domain.severity == Severity.HIGH

    assert domain.title == finding.title
    assert domain.description == finding.description

    assert domain.recommendations == [
        "Check container logs",
        "Review resource limits",
    ]

    assert len(domain.structured_evidences) == 1

    evidence = domain.structured_evidences[0]

    assert evidence.name == "restart_count"
    assert evidence.value == "10"
    assert evidence.type == EvidenceType.METRIC
    assert evidence.metadata == {"container": "api"}


def test_to_domain_handles_evidence_without_type() -> None:
    model = FindingMapper.to_model(
        Finding(
            rule="memory",
            kind=FindingKind.OBSERVATION,
            severity=Severity.HIGH,
            title="Memory issue",
            description="High memory",
            structured_evidences=[
                Evidence(name="memory", value="512Mi", source=EvidenceType.METRIC)
            ],
        ),
        analysis_id="123",
    )
    domain = FindingMapper.to_domain(model)

    assert len(domain.structured_evidences) == 1
    assert domain.structured_evidences[0].type is None


def test_finding_mapper_round_trip(finding: Finding) -> None:
    model = FindingMapper.to_model(finding, analysis_id="123")
    restored = FindingMapper.to_domain(model)

    assert restored.rule == finding.rule
    assert restored.kind == finding.kind
    assert restored.severity == finding.severity
    assert restored.title == finding.title
    assert restored.description == finding.description
    assert restored.recommendations == finding.recommendations
