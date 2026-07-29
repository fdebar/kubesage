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
