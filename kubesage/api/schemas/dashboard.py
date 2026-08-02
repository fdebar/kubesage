from datetime import datetime

from pydantic import BaseModel

from kubesage.models.finding import Severity


class DashboardSummary(BaseModel):
    """Represents the overall security posture of the cluster."""

    total_analyses: int
    total_findings: int
    critical_findings: int
    high_findings: int
    last_analysis_at: datetime | None


class DashboardRecentAnalysis(BaseModel):
    """A single recent analysis entry for the dashboard."""

    id: str
    namespace: str
    pod: str
    severity: Severity
    created_at: datetime


class DashboardAnalysisItem(BaseModel):
    """Response model for a single analysis item on the dashboard"""

    id: str
    namespace: str
    pod: str
    severity: str | None
    created_at: datetime
    duration_ms: int


class DashboardOverviewResponse(BaseModel):
    """Response model for dashboard overview"""

    total_analyses: int
    critical_count: int
    high_count: int

    latest_analyses: list[DashboardAnalysisItem]
