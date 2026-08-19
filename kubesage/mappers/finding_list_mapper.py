from kubesage.api.schemas.finding import FindingListItemResponse
from kubesage.models.finding_list_item import FindingListItem


class FindingListMapper:
    @staticmethod
    def to_response(findings: list[FindingListItem]) -> list[FindingListItemResponse]:
        return [
            FindingListItemResponse(
                id=finding.id,
                analysis_id=finding.analysis_id,
                rule=finding.rule,
                kind=finding.kind,
                severity=finding.severity,
                title=finding.title,
                description=finding.description,
                resource=finding.resource,
                created_at=finding.created_at,
            )
            for finding in findings
        ]
