from dataclasses import dataclass


@dataclass(slots=True)
class Event:
    reason: str
    message: str
    last_timestamp: str
