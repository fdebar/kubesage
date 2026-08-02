from pydantic import BaseModel, Field


class AIReport(BaseModel):
    summary: str
    root_cause: str | None = None
    evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    additional_investigations: list[str] = Field(default_factory=list)
