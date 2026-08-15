from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from kubesage.models.analysis import AnalysisTrigger
from kubesage.services.analysis_service import AnalysisService


@pytest.fixture
def incident_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repository() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(incident_service: MagicMock, repository: MagicMock) -> AnalysisService:
    return AnalysisService(incident_service=incident_service, repository=repository)


@patch("kubesage.services.analysis_service.ANALYSIS_DURATION")
@patch("kubesage.services.analysis_service.ANALYSIS_TOTAL")
def test_analyze_success(
    mock_total: MagicMock,
    mock_duration: MagicMock,
    service: AnalysisService,
    incident_service: MagicMock,
    repository: MagicMock,
) -> None:
    analysis = MagicMock()
    incident_service.analyze.return_value = analysis
    result = service.analyze("default", "my-pod", AnalysisTrigger.API)

    assert result is analysis

    incident_service.analyze.assert_called_once_with(
        "default", "my-pod", AnalysisTrigger.API
    )
    repository.save.assert_called_once_with(analysis)

    mock_total.labels.assert_called_once_with(status="success")
    mock_total.labels.return_value.inc.assert_called_once()

    mock_duration.observe.assert_called_once()


@patch("kubesage.services.analysis_service.ANALYSIS_DURATION")
@patch("kubesage.services.analysis_service.ANALYSIS_TOTAL")
def test_analyze_records_error(
    mock_total: MagicMock,
    mock_duration: MagicMock,
    service: AnalysisService,
    incident_service: MagicMock,
) -> None:
    incident_service.analyze.side_effect = RuntimeError("Analysis failed")

    with pytest.raises(RuntimeError, match="Analysis failed"):
        service.analyze("default", "my-pod", AnalysisTrigger.API)

    mock_total.labels.assert_called_once_with(status="error")
    mock_total.labels.return_value.inc.assert_called_once()

    mock_duration.observe.assert_called_once()


@patch("kubesage.services.analysis_service.ANALYSIS_DURATION")
@patch("kubesage.services.analysis_service.ANALYSIS_TOTAL")
def test_analyze_repository_error(
    mock_total: MagicMock,
    mock_duration: MagicMock,
    service: AnalysisService,
    incident_service: MagicMock,
    repository: MagicMock,
) -> None:
    analysis = MagicMock()
    incident_service.analyze.return_value = analysis
    repository.save.side_effect = RuntimeError("Database error")

    with pytest.raises(RuntimeError, match="Database error"):
        service.analyze("default", "my-pod", AnalysisTrigger.API)

    mock_total.labels.assert_called_once_with(status="error")
    mock_duration.observe.assert_called_once()


def test_get(service: AnalysisService, repository: MagicMock) -> None:
    analysis_id = uuid4()
    analysis = MagicMock()

    repository.get.return_value = analysis

    assert service.get(analysis_id) is analysis

    repository.get.assert_called_once_with(analysis_id)


def test_list_analyses(service: AnalysisService, repository: MagicMock) -> None:
    repository.list_analyses.return_value = []

    result = service.list_analyses(limit=10, offset=20)

    assert result == []

    repository.list_analyses.assert_called_once_with(limit=10, offset=20)


def test_list_summaries(service: AnalysisService, repository: MagicMock) -> None:
    repository.list_summaries.return_value = []

    result = service.list_summaries(limit=10, offset=20)

    assert result == []

    repository.list_summaries.assert_called_once_with(limit=10, offset=20)


def test_count(service: AnalysisService, repository: MagicMock) -> None:
    repository.count.return_value = 42

    assert service.count() == 42

    repository.count.assert_called_once_with()
