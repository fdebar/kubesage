from dataclasses import dataclass


@dataclass(slots=True)
class AIReport:
    severity: str
    summary: str
    root_cause: str
    recommendations: list[str]
    kubectl_commands: list[str]
