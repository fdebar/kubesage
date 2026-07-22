from fastapi import APIRouter
from fastapi import Depends
from api.dependencies import get_incident_service
from api.schemas import AnalyzeRequest
from api.schemas import AnalyzeResponse

router = APIRouter(
    tags=["Analysis"],
)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    request: AnalyzeRequest,
    service=Depends(get_incident_service),
):
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
