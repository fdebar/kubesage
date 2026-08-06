from fastapi import APIRouter, Depends, HTTPException, status

from kubesage.api.dependencies import get_analysis_service
from kubesage.api.mappers import to_response
from kubesage.api.schemas.request import AnalyzeRequest
from kubesage.api.schemas.response import AnalyzeResponse
from kubesage.models.analysis import AnalysisTrigger
from kubesage.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("", response_model=AnalyzeResponse)
def analyze(
    body: AnalyzeRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalyzeResponse:
    """Analyze an incident."""

    analysis = analysis_service.analyze(body.namespace, body.pod, AnalysisTrigger.API)
    if analysis.report is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis could not produce a report",
        )

    return to_response(analysis.report.model_dump())
