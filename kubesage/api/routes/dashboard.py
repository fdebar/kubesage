from fastapi import APIRouter, Depends

from kubesage.api.dependencies import get_dashboard_service
from kubesage.api.schemas.dashboard import DashboardOverviewResponse
from kubesage.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def overview(
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardOverviewResponse:
    """
    Get dashboard overview.

    Returns:
        DashboardOverviewResponse: Dashboard overview.
    """

    return service.overview()
