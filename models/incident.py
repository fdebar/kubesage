from dataclasses import dataclass, field

from models.container import ContainerInfo


@dataclass(slots=True)
class Incident:
    namespace: str
    pod: str

    phase: str

    logs: str

    containers: list[ContainerInfo]

    events: list[dict] = field(default_factory=list)