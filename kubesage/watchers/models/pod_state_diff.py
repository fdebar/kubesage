from pydantic import BaseModel


class PodStateDiff(BaseModel):
    """
    Represents the evolution of a Pod between two observations.
    """

    previous_phase: str | None = None
    current_phase: str | None = None
    phase_changed: bool = False
    previous_restart_count: int = 0
    current_restart_count: int = 0
    restart_delta: int = 0
    image_changed: bool = False
    deleted: bool = False
