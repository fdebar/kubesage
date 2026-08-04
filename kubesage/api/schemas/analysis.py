from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

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
    phase: str


class AIReportResponse(BaseModel):
    """API representation of an AI report."""

    summary: str
    root_cause: str | None
    evidence: list[str]
    recommendations: list[str]
    additional_investigations: list[str]


class AnalysisResponse(BaseModel):
    """API representation of an analysis."""

    id: UUID
    incident: IncidentResponse
    findings: list[FindingDetailResponse]
    report: AIReportResponse | None
    created_at: datetime
    duration_ms: int


class ContainerResponse(BaseModel):
    """API representation of a container."""

    name: str
    image: str
    ready: bool
    restart_count: int
    waiting_reason: str | None
    waiting_message: str | None
    last_exit_code: int | None
    last_exit_reason: str | None


class EventResponse(BaseModel):
    """API representation of a Kubernetes event."""

    type: str
    reason: str
    message: str
    last_timestamp: float | None


class ContainerMetricsResponse(BaseModel):
    """API representation of container metrics."""

    name: str
    cpu_usage: float
    memory_usage: int
    cpu_limit: float | None
    memory_limit: int | None
    cpu_throttling_ratio: float | None


class PodMetricsResponse(BaseModel):
    """API representation of pod metrics."""

    containers: list[ContainerMetricsResponse]
