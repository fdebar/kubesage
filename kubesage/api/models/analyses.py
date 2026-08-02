from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class Severity(StrEnum):
    """The severity of an analysis."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RecentAnalysis(BaseModel):
    """A single recent analysis entry."""

    id: str
    namespace: str
    pod: str
    severity: Severity
    created_at: datetime
