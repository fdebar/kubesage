from fastapi import APIRouter, Depends
from api.dependencies import get_incident_service
from api.schemas import AnalyzeRequest, AnalyzeResponse
from services.incident_service import IncidentService

router = APIRouter(
    tags=["Analysis"],
)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    request: AnalyzeRequest,
    service: IncidentService = Depends(get_incident_service),
) -> AnalyzeResponse:
    report = service.analyze(
        namespace=request.namespace,
        pod=request.pod,
    )

    return AnalyzeResponse(
        summary=report.get("summary", ""),
        severity=report.get("severity", "Unknown"),
        root_cause=report.get("root_cause", ""),
        recommendations=report.get("recommendations", []),
        kubectl_commands=report.get("kubectl_commands", []),
    )
