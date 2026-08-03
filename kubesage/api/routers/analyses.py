from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from kubesage.api.dependencies import get_analysis_repository
from kubesage.api.schemas.analysis import (
    AnalysisResponse,
)
from kubesage.mappers.analysis_mapper import AnalysisMapper
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
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    return AnalysisMapper.to_detail_response(analysis)


@router.get("", response_model=list[AnalysisResponse])
def list_analyses(
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> list[AnalysisResponse] | None:
    analyses = repository.list_recent()
    if not analyses:
        return None

    return [AnalysisMapper.to_detail_response(analysis) for analysis in analyses]
