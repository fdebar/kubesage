from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from kubesage.api.dependencies import get_analysis_repository
from kubesage.api.schemas.analysis import (
    AnalysisResponse,
)
from kubesage.api.schemas.analysis_summary import AnalysisSummaryResponse
from kubesage.api.schemas.paginated_response import PaginatedResponse
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


@router.get("", response_model=PaginatedResponse[AnalysisSummaryResponse])
def list_analyses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> PaginatedResponse[AnalysisSummaryResponse]:
    offset = (page - 1) * page_size

    analyses = repository.list_summaries(
        limit=page_size,
        offset=offset,
    )

    return PaginatedResponse(
        items=AnalysisSummaryMapper.to_response(analyses),
        total=repository.count(),
        page=page,
        page_size=page_size,
    )
