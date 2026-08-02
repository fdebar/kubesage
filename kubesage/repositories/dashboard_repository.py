from datetime import datetime

from kubesage.api.models.dashboard import DashboardRecentAnalysis, DashboardSummary
from kubesage.models.finding import Severity


class DashboardRepository:
    """Repository for dashboard data."""

    def get_summary(self) -> DashboardSummary:
        """Get the dashboard summary."""

        return DashboardSummary(
            total_analyses=0,
            total_findings=0,
            critical_findings=0,
            last_analysis_at=None,
        )

    def get_recent_analyses(self, limit: int = 5) -> list[DashboardRecentAnalysis]:
        """Get recent analyses."""

        return [
            DashboardRecentAnalysis(
                id="1",
                namespace="default",
                pod="pod-1",
                severity=Severity.CRITICAL,
                created_at=datetime.now(),
            )
        ]
