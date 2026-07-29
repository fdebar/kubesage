from enum import StrEnum
from typing import Any

from pydantic import BaseModel


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
    value: str | None = None
    source: str | None = None
    type: EvidenceType | None
    unit: str | None = None
    metadata: dict[str, Any] = {}
