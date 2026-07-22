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
