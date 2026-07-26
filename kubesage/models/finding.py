from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Severity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def weight(self) -> int:
        return {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.WARNING: 2,
            Severity.MEDIUM: 3,
            Severity.HIGH: 4,
            Severity.CRITICAL: 5,
        }[self]


class ResourceRef(BaseModel):
    api_version: str | None = None
    kind: str
    namespace: str | None = None
    name: str


class Finding(BaseModel):
    """Result produced by a Rule."""

    rule: str
    severity: Severity
    title: str
    description: str
    resource: ResourceRef

    evidences: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    confidence: float = 1.0
