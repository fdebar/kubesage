from fastapi import APIRouter, Depends

from kubesage.api.dependencies import get_analysis_repository
from kubesage.api.models.analysis import AnalysisResponse
from kubesage.repositories.analysis_repository import AnalysisRepository

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.get("", response_model=list[AnalysisResponse])
def list_analyses(
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> list[AnalysisResponse] | None:
    analyses = repository.list_recent()
    if not analyses:
        return None

    return [
        AnalysisResponse(
            id=analysis.id,
            namespace=analysis.incident.namespace,
            pod=analysis.incident.pod,
            severity=(analysis.findings[0].severity if analysis.findings else None),
            created_at=analysis.created_at,
            duration_ms=analysis.duration_ms,
        )
        for analysis in analyses
    ]
