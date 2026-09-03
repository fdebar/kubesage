from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from kubesage.models.finding import Severity


class AnalysisSummaryResponse(BaseModel):
    """API representation of an analysis summary."""

    id: UUID
    namespace: str
    pod: str
    phase: str
    highest_severity: Severity | None
    summary: str | None
    findings_count: int
    duration_ms: int
    created_at: datetime
    trace_id: str | None
