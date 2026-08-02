from kubesage.api.schemas.dashboard import (
    DashboardAnalysisItem,
    DashboardOverviewResponse,
)
from kubesage.repositories.analysis_repository import AnalysisRepository


class DashboardService:
    def __init__(self, repository: AnalysisRepository) -> None:
        self.repository = repository

    def overview(self) -> DashboardOverviewResponse:
        """Get dashboard overview"""

        analyses = self.repository.list_recent(limit=10)
        if not analyses:
            return DashboardOverviewResponse(
                total_analyses=0,
                critical_count=0,
                high_count=0,
                latest_analyses=[],
            )

        return DashboardOverviewResponse(
            total_analyses=self.repository.count(),
            critical_count=self.repository.count_by_severity("CRITICAL"),
            high_count=self.repository.count_by_severity("HIGH"),
            latest_analyses=[
                DashboardAnalysisItem(
                    id=str(a.id),
                    namespace=a.incident.namespace,
                    pod=a.incident.pod,
                    severity=a.highest_severity,
                    created_at=a.created_at,
                    duration_ms=a.duration_ms,
                )
                for a in analyses
            ],
        )
