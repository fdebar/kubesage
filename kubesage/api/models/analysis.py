from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from kubesage.models.finding import Severity


class AnalysisResponse(BaseModel):
    """API representation of an analysis."""

    id: UUID
    namespace: str
    pod: str
    severity: Severity | None
    created_at: datetime
    duration_ms: int
