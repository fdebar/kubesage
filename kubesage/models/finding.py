from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from kubesage.models.evidence import Evidence


class FindingKind(StrEnum):
    OBSERVATION = "observation"
    DIAGNOSIS = "diagnosis"


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

    kind: FindingKind = FindingKind.OBSERVATION
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    confidence: float = 1.0

    related_findings: list[str] = Field(default_factory=list)
    caused_by: list[str] = Field(default_factory=list)

    evidences: list[str] = Field(
        default_factory=list
    )  # TODO: It will be replaced by structured_evidences later
    structured_evidences: list[Evidence] = Field(default_factory=list)
