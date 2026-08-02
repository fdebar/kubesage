from kubesage.api.models.dashboard import DashboardResponse
from kubesage.repositories import dashboard_repository


class DashboardService:
    """Service for dashboard data."""

    def __init__(self, repository: dashboard_repository.DashboardRepository):
        self.repository = repository

    def get_dashboard(self) -> DashboardResponse:
        """Get the dashboard response."""

        summary = self.repository.get_summary()
        recent_analyses = self.repository.get_recent_analyses()

        return DashboardResponse(
            summary=summary,
            recent_analyses=recent_analyses,
        )
