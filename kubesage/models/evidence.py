from enum import StrEnum
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field


class EvidenceType(StrEnum):
    METRIC = "metric"
    LOG = "log"
    EVENT = "event"
    POD_STATE = "pod_state"
    CONTAINER_STATE = "container_state"
    CORRELATION = "correlation"
    THRESHOLD = "threshold"


class Evidence(BaseModel):
    """
    Structured evidence supporting a finding.
    """

    name: str
    description: str | None = None
    source: str | None = None
    type: EvidenceType | None = None
    unit: str | None = None
    value: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def id(self) -> str:
        raw = "|".join(
            [
                self.type.value if self.type else "",
                self.name,
                self.value or "",
                self.source or "",
            ]
        )
        return sha256(raw.encode()).hexdigest()[:12]
