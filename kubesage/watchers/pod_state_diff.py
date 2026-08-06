from pydantic import BaseModel


class PodStateDiff(BaseModel):
    """
    Represents the difference in state between two Pod snapshots, focused on
    restart counts and phase transitions.
    """

    restart_delta: int = 0
    phase_changed: bool = False
    previous_phase: str | None = None
    current_phase: str | None = None
