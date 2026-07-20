from dataclasses import asdict
import json
from dataclasses import dataclass, field


@dataclass(slots=True)
class Report:

    severity: str

    summary: str

    findings: list[str] = field(default_factory=list)

    recommendations: list[str] = field(default_factory=list)

    commands: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self))