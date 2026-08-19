from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ServiceStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class ServiceTestResponse(BaseModel):
    status: ServiceStatus
    checked_at: datetime
    latency_ms: int | None = None
    message: str | None = None
