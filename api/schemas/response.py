from pydantic import BaseModel, Field


class AnalyzeResponse(BaseModel):
    summary: str = Field(
        description="Short AI-generated summary",
        examples=["The pod is in CrashLoopBackOff because Redis is unreachable."],
    )
    severity: str = Field(
        examples=["critical"],
    )
    root_cause: str
    recommendations: list = Field(default_factory=list)
    kubectl_commands: list = Field(default_factory=list)


class FindingResponse(BaseModel):
    title: str
    description: str
    severity: str


class AnalyzeDetailedResponse(AnalyzeResponse):
    findings: list[FindingResponse]
    metrics: dict[str, float | int | str]
    events: list[str]


class DebugResponse(BaseModel):
    incident: dict
    findings: list[FindingResponse]
    prompt: str
    ai_report: AnalyzeResponse
