from fastapi import APIRouter, Depends

from kubesage.api.dependencies import get_incident_service
from kubesage.api.mappers import to_response
from kubesage.api.schemas.request import AnalyzeRequest
from kubesage.api.schemas.response import AnalyzeResponse
from kubesage.services.incident_service import IncidentService

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("", response_model=AnalyzeResponse)
def analyze(
    body: AnalyzeRequest,
    service: IncidentService = Depends(get_incident_service),
) -> AnalyzeResponse:
    """Analyze a Kubernetes incident."""

    analysis = service.analyze(
        namespace=body.namespace,
        pod=body.pod,
    )

    return to_response(analysis.report.model_dump())
