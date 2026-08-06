from pydantic import BaseModel, Field

from kubesage.api.schemas.finding import FindingResponse


class AnalyzeResponse(BaseModel):
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
    evidence: list[str] = Field(
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


class AnalyzeDetailedResponse(AnalyzeResponse):
    findings: list[FindingResponse]
    metrics: dict[str, float | int | str]
    events: list[str]


class DebugResponse(BaseModel):
    incident: dict
    findings: list[FindingResponse]
    prompt: str
    ai_report: AnalyzeResponse
