from typing import Any

from pydantic import BaseModel


class Evidence(BaseModel):
    """
    Structured evidence supporting a finding.
    """

    type: str
    name: str
    value: Any
    source: str | None = None
    unit: str | None = None
    metadata: dict[str, Any] = {}
