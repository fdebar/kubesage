from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from kubesage.models.ai_report import AIReport
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident


class Analysis(BaseModel):
    """Represents an analysis of an incident."""

    id: UUID = Field(default_factory=uuid4)
    incident: Incident
    findings: list[Finding]
    report: AIReport | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int

    @property
    def highest_severity(self) -> str | None:
        if not self.findings:
            return None

        return max(self.findings, key=lambda f: f.severity.weight).severity.value
