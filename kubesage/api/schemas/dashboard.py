from datetime import datetime

from pydantic import BaseModel

from kubesage.models.finding import Severity


class ClusterStatus(BaseModel):
    name: str
    version: str
    status: str


class DashboardMetrics(BaseModel):
    pods: int
    nodes: int
    analyses: int
    findings: int
    health_score: int


class SeveritySummary(BaseModel):
    critical: int
    high: int
    warning: int
    low: int
    info: int


class DashboardAnalysisItem(BaseModel):
    """Response model for a single analysis item on the dashboard"""

    id: str
    namespace: str
    pod: str
    severity: Severity | None
    created_at: datetime
    duration_ms: int


class DashboardOverviewResponse(BaseModel):
    """Response model for dashboard overview"""

    cluster: ClusterStatus
    metrics: DashboardMetrics
    severities: SeveritySummary
    latest_analyses: list[DashboardAnalysisItem]
