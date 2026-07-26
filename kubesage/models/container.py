from dataclasses import dataclass


@dataclass(slots=True)
class ContainerInfo:
    name: str
    image: str
    ready: bool
    restart_count: int

    waiting_reason: str | None = None
    waiting_message: str | None = None

    last_exit_code: int | None = None
    last_exit_reason: str | None = None
