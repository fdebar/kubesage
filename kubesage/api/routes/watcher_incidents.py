from typing import Literal

from fastapi import APIRouter, Depends, Query

from kubesage.api.dependencies import get_watcher_incident_repository
from kubesage.api.schemas.paginated_response import PaginatedResponse
from kubesage.api.schemas.watcher_incident import WatcherIncidentResponse
from kubesage.repositories.watcher_incident_repository import (
    WatcherIncidentRepository,
)

router = APIRouter(prefix="/watcher/incidents", tags=["Watcher incidents"])


@router.get("", response_model=PaginatedResponse[WatcherIncidentResponse])
def list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Literal["active", "resolved"] | None = None,
    namespace: str | None = None,
    repository: WatcherIncidentRepository = Depends(get_watcher_incident_repository),
) -> PaginatedResponse[WatcherIncidentResponse]:
    offset = (page - 1) * page_size
    incidents = repository.list_incidents(
        limit=page_size,
        offset=offset,
        status=status,
        namespace=namespace,
    )

    return PaginatedResponse(
        items=[WatcherIncidentResponse.model_validate(item) for item in incidents],
        total=repository.count(status=status, namespace=namespace),
        page=page,
        page_size=page_size,
    )
