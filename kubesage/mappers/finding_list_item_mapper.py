from datetime import datetime
from uuid import UUID

from kubesage.database.models.finding import FindingModel
from kubesage.models.finding import FindingKind, ResourceRef, Severity
from kubesage.models.finding_list_item import FindingListItem


class FindingListItemMapper:
    @staticmethod
    def to_domain(finding: FindingModel, created_at: datetime) -> FindingListItem:
        resource = None

        if finding.resource_kind and finding.resource_name:
            resource = ResourceRef(
                api_version=finding.resource_api_version,
                kind=finding.resource_kind,
                namespace=finding.resource_namespace,
                name=finding.resource_name,
            )

        return FindingListItem(
            id=UUID(finding.id),
            analysis_id=UUID(finding.analysis_id),
            rule=finding.rule,
            kind=FindingKind(finding.kind),
            severity=Severity(finding.severity),
            title=finding.title,
            description=finding.description,
            resource=resource,
            created_at=created_at,
        )
