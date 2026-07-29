from pydantic import BaseModel

from kubesage.models.events import Event
from kubesage.models.finding import Finding


class PromptContext(BaseModel):
    namespace: str
    pod: str
    phase: str
    logs: str
    events: list[Event]
    findings: list[Finding]
