from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class Finding:
    severity: Severity
    title: str
    description: str
    confidence: float
    source: str
    category: str
    evidence: list[str]
