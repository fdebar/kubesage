from api.mappers import to_response
from fastapi import APIRouter, Depends
from api.dependencies import get_incident_service
from api.schemas.request import AnalyzeRequest
from api.schemas.response import AnalyzeResponse
from services.incident_service import IncidentService

router = APIRouter(
    tags=["Analysis"],
)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    request: AnalyzeRequest,
    detailed: bool = False,
    service: IncidentService = Depends(get_incident_service),
) -> AnalyzeResponse:
    report = service.analyze(
        namespace=request.namespace,
        pod=request.pod,
    )

    return to_response(report)
