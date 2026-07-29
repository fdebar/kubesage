from datetime import datetime

from pydantic import BaseModel


class Event(BaseModel):
    type: str
    reason: str
    message: str
    last_timestamp: datetime | None
