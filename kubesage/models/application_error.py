from enum import StrEnum

from pydantic import BaseModel, Field


class ApplicationErrorKind(StrEnum):
    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    HTTP_5XX = "http_5xx"
    EXCEPTION = "exception"
    GENERIC_ERROR = "generic_error"


class ApplicationErrorGroup(BaseModel):
    fingerprint: str
    kind: ApplicationErrorKind
    domain: str | None = None
    occurrences: int
    first_seen: str
    last_seen: str
    example_messages: list[str] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
