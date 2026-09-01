import pytest

from kubesage.models.ai_report import AIReport, FindingReference


def test_ai_report_confidence_range() -> None:
    report = AIReport(summary="Test", confidence=0.95)
    assert report.confidence == 0.95


def test_ai_report_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        AIReport(summary="Test", confidence=2.0)


def test_ai_report_finding_reference() -> None:
    report = AIReport(
        summary="Test",
        findings=[
            FindingReference(
                rule="memory_exhaustion",
                description="Memory exhaustion detected.",
            )
        ],
    )

    assert len(report.findings) == 1
    assert report.findings[0].rule == "memory_exhaustion"


def test_ai_report_findings_default_to_empty() -> None:
    report = AIReport(summary="Test")

    assert report.findings == []
