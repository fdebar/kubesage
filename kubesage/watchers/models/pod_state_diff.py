from pydantic import BaseModel


class PodStateDiff(BaseModel):
    """
    Represents the difference in state between two Pod snapshots, focused on
    restart counts and phase transitions.
    """

    previous_phase: str | None = None
    current_phase: str | None = None
    phase_changed: bool = False

    previous_restart_count: int = 0
    current_restart_count: int = 0
    restart_delta: int = 0

    previous_waiting_reason: str | None = None
    current_waiting_reason: str | None = None
    waiting_reason_changed: bool = False

    previous_ready: bool = False
    current_ready: bool = False
    ready_changed: bool = False

    oom_killed: bool = False
