from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from kubesage.models.ai_report import EvidenceReference
from kubesage.models.evidence import EvidenceType
from kubesage.models.finding import FindingKind, Severity


class ResourceResponse(BaseModel):
    """API representation of a resource."""

    api_version: str | None
    kind: str
    namespace: str | None
    name: str


class EvidenceResponse(BaseModel):
    """API representation of an evidence."""

    name: str
    value: str | None
    source: str | None
    type: EvidenceType | None
    unit: str | None
    metadata: dict


class FindingDetailResponse(BaseModel):
    """API representation of a finding."""

    rule: str
    severity: Severity
    kind: FindingKind
    title: str
    description: str
    resource: ResourceResponse | None
    recommendations: list[str]
    priority: int
    confidence: float
    related_findings: list[str]
    caused_by: list[str]
    evidences: list[EvidenceResponse]


class IncidentResponse(BaseModel):
    """API representation of an incident."""

    namespace: str
    pod: str
    pod_uid: str | None = None
    phase: str


class AIReportResponse(BaseModel):
    """API representation of an AI report."""

    summary: str = Field(description="Short summary of the incident.")
    root_cause: str | None = Field(
        default=None,
        description="Most likely root cause of the incident.",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1.",
    )
    impact: str | None = Field(
        default=None,
        description="User or system impact caused by the incident.",
    )
    evidence: list[EvidenceReference] = Field(
        default_factory=list,
        description="Evidence supporting the analysis.",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommended remediation actions.",
    )
    additional_investigations: list[str] = Field(
        default_factory=list,
        description="Additional checks suggested by the AI.",
    )


class AnalysisResponse(BaseModel):
    """API representation of an analysis."""

    id: UUID
    incident: IncidentResponse
    findings: list[FindingDetailResponse]
    report: AIReportResponse | None
    created_at: datetime
    duration_ms: int
