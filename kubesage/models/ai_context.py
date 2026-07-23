from dataclasses import dataclass

from kubesage.models.finding import Finding
from kubesage.models.incident import Incident


@dataclass(slots=True)
class AIContext:
    incident: Incident
    findings: list[Finding]
    summary: str
    metrics_summary: str
