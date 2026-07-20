from dataclasses import dataclass, field


@dataclass(slots=True)
class Report:

    severity: str

    summary: str

    findings: list[str] = field(default_factory=list)

    recommendations: list[str] = field(default_factory=list)

    kubectl_commands: list[str] = field(default_factory=list)
    