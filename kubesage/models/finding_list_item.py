from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from kubesage.models.finding import FindingKind, ResourceRef, Severity


class FindingListItem(BaseModel):
    """A persisted finding as displayed in the findings list."""

    id: UUID
    analysis_id: UUID
    rule: str
    kind: FindingKind
    severity: Severity
    title: str
    description: str
    resource: ResourceRef | None = None
    created_at: datetime
