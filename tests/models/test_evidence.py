from kubesage.models.evidence import Evidence, EvidenceType


def test_evidence_creation() -> None:

    evidence = Evidence(
        type=EvidenceType.METRIC,
        name="memory_usage",
        value="850",
        unit="Mi",
    )

    assert evidence.type == "metric"
    assert evidence.value == "850"


def test_evidence_description_is_optional() -> None:
    evidence = Evidence(
        name="restart_count",
        value="10",
    )

    assert evidence.description is None


def test_evidence_supports_human_description() -> None:
    evidence = Evidence(
        name="restart_count",
        value="10",
        type=EvidenceType.CONTAINER_STATE,
        source="kubernetes",
        description="Container restarted repeatedly.",
    )

    assert evidence.description == "Container restarted repeatedly."


def test_evidence_metadata_default_is_not_shared() -> None:
    first = Evidence(name="test")
    second = Evidence(name="test")

    first.metadata["key"] = "value"

    assert second.metadata == {}


def test_evidence_id_is_stable() -> None:
    evidence = Evidence(
        type=EvidenceType.METRIC,
        name="memory_usage",
        value="64Mi",
        source="prometheus",
    )

    assert evidence.id == evidence.id
    assert len(evidence.id) == 12


def test_different_evidence_has_different_id() -> None:
    first = Evidence(
        type=EvidenceType.METRIC,
        name="memory_usage",
        value="64Mi",
        source="prometheus",
    )
    second = Evidence(
        type=EvidenceType.METRIC,
        name="memory_usage",
        value="128Mi",
        source="prometheus",
    )

    assert first.id != second.id
