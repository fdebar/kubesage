from datetime import datetime

from pydantic import BaseModel

from kubesage.api.models.analyses import Severity


class DashboardSummary(BaseModel):
    """Represents the overall security posture of the cluster."""

    total_analyses: int
    total_findings: int
    critical_findings: int
    last_analysis_at: datetime | None


class DashboardRecentAnalysis(BaseModel):
    """A single recent analysis entry for the dashboard."""

    id: str
    namespace: str
    pod: str
    severity: Severity
    created_at: datetime


class DashboardResponse(BaseModel):
    """Represents the full dashboard response."""

    summary: DashboardSummary
    recent_analyses: list[DashboardRecentAnalysis]
