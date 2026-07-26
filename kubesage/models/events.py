from dataclasses import dataclass


@dataclass(slots=True)
class Event:
    type: str
    reason: str
    message: str
    last_timestamp: str
