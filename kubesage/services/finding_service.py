from kubesage.models.finding_list_item import FindingListItem
from kubesage.repositories.finding_repository import FindingRepository


class FindingService:
    def __init__(self, repository: FindingRepository) -> None:
        self.repository = repository

    def list_findings(self, limit: int = 50, offset: int = 0) -> list[FindingListItem]:
        return self.repository.list_findings(
            limit=limit,
            offset=offset,
        )

    def count(self) -> int:
        return self.repository.count()
