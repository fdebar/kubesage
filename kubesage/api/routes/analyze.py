from fastapi import APIRouter, Depends, HTTPException, status

from kubesage.api.dependencies import get_analysis_service
from kubesage.api.schemas.analysis import AnalysisResponse
from kubesage.api.schemas.request import AnalyzeRequest
from kubesage.mappers.analysis_mapper import AnalysisMapper
from kubesage.models.analysis import AnalysisTrigger
from kubesage.observability.metrics import ANALYSIS_TOTAL
from kubesage.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("", response_model=AnalysisResponse)
def analyze(
    body: AnalyzeRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisResponse:
    analysis = analysis_service.analyze(
        body.namespace,
        body.pod,
        AnalysisTrigger.API,
    )

    if analysis.report is None:
        ANALYSIS_TOTAL.labels(status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis could not produce a report",
        )

    return AnalysisMapper.to_detail_response(analysis)
