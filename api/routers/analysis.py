from services.incident_service import IncidentService
from api.mappers import to_response
from fastapi import APIRouter, Depends
from api.dependencies import get_incident_service
from api.schemas.request import AnalyzeRequest
from api.schemas.response import AnalyzeResponse

router = APIRouter(
    tags=["Analysis"],
)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    body: AnalyzeRequest,
    service: IncidentService = Depends(get_incident_service),
) -> AnalyzeResponse:
    report = service.analyze(
        namespace=body.namespace,
        pod=body.pod,
    )

    return to_response(report)
