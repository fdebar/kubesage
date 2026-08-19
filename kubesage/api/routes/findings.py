from fastapi import APIRouter, Depends, Query

from kubesage.api.dependencies import get_finding_repository
from kubesage.api.schemas.finding import FindingListItemResponse
from kubesage.api.schemas.paginated_response import PaginatedResponse
from kubesage.mappers.finding_list_mapper import FindingListMapper
from kubesage.repositories.finding_repository import FindingRepository

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("", response_model=PaginatedResponse[FindingListItemResponse])
def list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    repository: FindingRepository = Depends(get_finding_repository),
) -> PaginatedResponse[FindingListItemResponse]:
    offset = (page - 1) * page_size

    findings = repository.list_findings(
        limit=page_size,
        offset=offset,
    )

    return PaginatedResponse(
        items=FindingListMapper.to_response(findings),
        total=repository.count(),
        page=page,
        page_size=page_size,
    )
