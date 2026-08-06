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

    oom_killed: bool = False
