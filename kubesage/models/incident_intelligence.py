from enum import StrEnum

from pydantic import BaseModel, Field

from kubesage.models.finding import Finding
from kubesage.models.timeline import TimelineEvent


class CorrelationType(StrEnum):
    RELATED = "related"
    CAUSED_BY = "caused_by"


class Correlation(BaseModel):
    """Relationship between two findings."""

    source_finding: str
    target_finding: str
    type: CorrelationType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class RootCauseCandidate(BaseModel):
    """Potential root cause identified for an incident."""

    finding: str
    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_findings: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)


class IncidentIntelligence(BaseModel):
    """
    Structured intelligence derived from an incident analysis.

    This model connects findings, timeline events, evidence,
    correlations and root-cause candidates into a single
    structured representation.
    """

    findings: list[Finding] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    correlations: list[Correlation] = Field(default_factory=list)
    root_causes: list[RootCauseCandidate] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
