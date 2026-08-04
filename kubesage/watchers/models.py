from datetime import UTC, datetime

from kubernetes.client import V1Pod
from pydantic import BaseModel, ConfigDict, Field


class IncidentTrigger(BaseModel):
    """
    Represents an external signal that should trigger an analysis.
    """

    source: str = Field(default="kubernetes")
    reason: str
    namespace: str
    pod: str
    message: str | None = None
    occurred_at: datetime


class PodWatchEvent(BaseModel):
    """
    Internal representation of a Kubernetes pod watch event.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: str
    pod: V1Pod
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
