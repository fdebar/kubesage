from fastapi import APIRouter, Depends

from kubesage.api.dependencies import get_analysis_service
from kubesage.api.mappers import to_response
from kubesage.api.schemas.request import AnalyzeRequest
from kubesage.api.schemas.response import AnalyzeResponse
from kubesage.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("", response_model=AnalyzeResponse)
def analyze(
    body: AnalyzeRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalyzeResponse:
    """Analyze a Kubernetes incident."""

    analysis = service.analyze(
        namespace=body.namespace,
        pod=body.pod,
    )

    return to_response(analysis.report.model_dump())
