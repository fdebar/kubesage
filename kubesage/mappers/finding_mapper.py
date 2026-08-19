from kubesage.database.models import EvidenceModel, RecommendationModel
from kubesage.database.models.finding import FindingModel
from kubesage.models.evidence import Evidence, EvidenceType
from kubesage.models.finding import Finding, FindingKind, ResourceRef, Severity


class FindingMapper:
    @staticmethod
    def to_model(finding: Finding, analysis_id: str) -> FindingModel:
        """Map a Finding to a FindingModel."""

        finding_model = FindingModel(
            analysis_id=analysis_id,
            rule=finding.rule,
            kind=finding.kind.value,
            severity=finding.severity.value,
            title=finding.title,
            description=finding.description,
            resource_api_version=(
                finding.resource.api_version if finding.resource else None
            ),
            resource_kind=finding.resource.kind if finding.resource else None,
            resource_namespace=(
                finding.resource.namespace if finding.resource else None
            ),
            resource_name=finding.resource.name if finding.resource else None,
        )

        finding_model.evidences = [
            EvidenceModel(
                name=evidence.name,
                value=evidence.value,
                source=evidence.source,
                type=(evidence.type.value if evidence.type else None),
                unit=evidence.unit,
                evidence_metadata=evidence.metadata,
            )
            for evidence in finding.structured_evidences
        ]

        finding_model.recommendations = [
            RecommendationModel(text=r) for r in finding.recommendations
        ]

        return finding_model

    @staticmethod
    def to_domain(model: FindingModel) -> Finding:
        """Convert a FindingModel to a Finding."""

        resource = None
        if model.resource_kind and model.resource_name:
            resource = ResourceRef(
                api_version=model.resource_api_version,
                kind=model.resource_kind,
                namespace=model.resource_namespace,
                name=model.resource_name,
            )

        return Finding(
            rule=model.rule,
            kind=FindingKind(model.kind),
            severity=Severity(model.severity),
            title=model.title,
            description=model.description,
            resource=resource,
            recommendations=[r.text for r in model.recommendations],
            structured_evidences=[
                Evidence(
                    name=evidence.name,
                    value=evidence.value,
                    source=evidence.source,
                    type=(EvidenceType(evidence.type) if evidence.type else None),
                    unit=evidence.unit,
                    metadata=evidence.evidence_metadata or {},
                )
                for evidence in model.evidences
            ],
        )
