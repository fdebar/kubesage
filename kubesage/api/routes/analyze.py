from fastapi import APIRouter, Depends, HTTPException, status

from kubesage.api.dependencies import get_analysis_service
from kubesage.api.mappers import to_response
from kubesage.api.schemas.analysis import AIReportResponse
from kubesage.api.schemas.request import AnalyzeRequest
from kubesage.models.analysis import AnalysisTrigger
from kubesage.observability.metrics import ANALYSIS_TOTAL
from kubesage.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("", response_model=AIReportResponse)
def analyze(
    body: AnalyzeRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AIReportResponse:
    """Analyze an incident and return an AI report.

    Returns:
        AIReportResponse: AI report containing analysis results.

    Raises:
        HTTPException: If AI analysis could not produce a report.
    """

    analysis = analysis_service.analyze(body.namespace, body.pod, AnalysisTrigger.API)
    if analysis.report is None:
        ANALYSIS_TOTAL.labels(status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis could not produce a report",
        )

    return to_response(analysis.report.model_dump())
