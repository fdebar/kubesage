import pytest

from kubesage.models.ai_report import AIReport


def test_ai_report_confidence_range() -> None:
    report = AIReport(summary="Test", confidence=0.95)
    assert report.confidence == 0.95


def test_ai_report_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        AIReport(summary="Test", confidence=2.0)
