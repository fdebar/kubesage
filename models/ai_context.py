from dataclasses import dataclass
from models.finding import Finding
from models.incident import Incident


@dataclass(slots=True)
class AIContext:
    incident: Incident
    findings: list[Finding]
    summary: str
    metrics_summary: str
