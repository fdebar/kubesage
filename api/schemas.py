from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    namespace: str = Field(
        min_length=1,
        max_length=63,
        default="default",
        examples=["default"],
    )
    pod: str = Field(
        min_length=1,
        max_length=253,
        examples=["ai-demo-app"],
    )


class AnalyzeResponse(BaseModel):
    summary: str
    severity: str
    root_cause: str
    recommendations: list = Field(default_factory=list)
    kubectl_commands: list = Field(default_factory=list)
