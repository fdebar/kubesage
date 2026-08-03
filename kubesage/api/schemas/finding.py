from pydantic import BaseModel


class FindingResponse(BaseModel):
    title: str
    description: str
    severity: str
