from pydantic import BaseModel, Field

from kubesage.models.event import Event
from kubesage.models.finding import Finding
from kubesage.models.timeline import TimelineEvent


class PromptContext(BaseModel):
    namespace: str
    pod: str
    phase: str
    events: list[Event]
    findings: list[Finding]
    timeline: list[TimelineEvent] = Field(default_factory=list)
