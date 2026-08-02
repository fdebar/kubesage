from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class Severity(StrEnum):
    """The severity of an analysis."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    WARNING = "WARNING"


class RecentAnalysis(BaseModel):
    """A single recent analysis entry."""

    id: str
    namespace: str
    pod: str
    severity: Severity
    created_at: datetime


class AnalysisResponse(BaseModel):
    """A single analysis entry."""

    id: UUID
    namespace: str
    pod: str
    severity: Severity | None
    created_at: datetime
    duration_ms: int
