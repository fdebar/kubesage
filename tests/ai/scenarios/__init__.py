from dataclasses import dataclass, field

from kubesage.models.finding import Finding
from kubesage.models.incident import Incident
from kubesage.models.timeline import TimelineEvent


@dataclass(frozen=True)
class ReportQualityScenario:
    name: str
    incident: Incident
    findings: list[Finding]
    timeline: list[TimelineEvent] = field(default_factory=list)

    expected_root_cause_keywords: tuple[str, ...] = ()
    forbidden_root_cause_keywords: tuple[str, ...] = ()

    required_evidence_keywords: tuple[str, ...] = ()
    required_recommendation_keywords: tuple[str, ...] = ()

    require_root_cause: bool = False
    require_uncertainty: bool = False
