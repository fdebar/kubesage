from fastapi import APIRouter

from kubesage.api.models.dashboard import DashboardResponse
from kubesage.api.services import dashboard_service
from kubesage.repositories import dashboard_repository

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard() -> DashboardResponse:
    """Get the dashboard summary and recent analyses."""

    repository = dashboard_repository.DashboardRepository()
    service = dashboard_service.DashboardService(repository)
    result = service.get_dashboard()

    return result
