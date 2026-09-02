from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from kubesage.models.ai_report import AIReport
from kubesage.models.finding import Severity
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence


class AnalysisTrigger(StrEnum):
    API = "api"
    CLI = "cli"
    WATCHER = "watcher"


class Analysis(BaseModel):
    """Represents an analysis of an incident."""

    id: UUID = Field(default_factory=uuid4)
    trigger: AnalysisTrigger
    incident: Incident
    intelligence: IncidentIntelligence = Field(
        default_factory=IncidentIntelligence,
    )
    report: AIReport | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int

    @property
    def highest_severity(self) -> Severity | None:
        if not self.intelligence.findings:
            return None

        return max(self.intelligence.findings, key=lambda f: f.severity.weight).severity
