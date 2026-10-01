from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class WatcherIncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    namespace: str
    pod: str
    pod_uid: str
    reason: str
    status: Literal["active", "resolved"]
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None
    last_resource_version: str | None
    message: str | None
    analysis_id: str | None
