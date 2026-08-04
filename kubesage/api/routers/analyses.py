from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from kubesage.api.dependencies import get_analysis_repository
from kubesage.api.schemas.analysis import (
    AnalysisResponse,
)
from kubesage.api.schemas.analysis_summary import AnalysisSummaryResponse
from kubesage.mappers.analysis_mapper import AnalysisMapper
from kubesage.mappers.analysis_summary_mapper import AnalysisSummaryMapper
from kubesage.repositories.analysis_repository import AnalysisRepository

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: UUID,
    repository: AnalysisRepository = Depends(
        get_analysis_repository,
    ),
) -> AnalysisResponse:
    analysis = repository.get(analysis_id)

    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisMapper.to_detail_response(analysis)


@router.get("", response_model=list[AnalysisSummaryResponse])
def list_analyses(
    limit: int = 20,
    offset: int = 0,
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> list[AnalysisSummaryResponse]:
    analyses = repository.list_summaries(limit=limit, offset=offset)

    return AnalysisSummaryMapper.to_response(analyses)
