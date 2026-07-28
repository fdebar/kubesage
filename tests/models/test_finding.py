from kubesage.models.finding import (
    Finding,
    FindingKind,
    ResourceRef,
    Severity,
)


def test_finding_default_kind() -> None:
    finding = Finding(
        rule="test_rule",
        severity=Severity.HIGH,
        title="Test",
        description="Test finding",
        resource=ResourceRef(
            kind="Pod",
            name="test",
        ),
    )

    assert finding.kind == FindingKind.OBSERVATION
    assert finding.caused_by == []
