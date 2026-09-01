from kubesage.api.schemas.analysis import (  # noqa: F401
    CorrelationResponse,
    IncidentIntelligenceResponse,
    RootCauseCandidateResponse,
)
from kubesage.models.incident_intelligence import IncidentIntelligence


class IncidentIntelligentMapper:
    """Mapper for analysis summary."""

    @staticmethod
    def to_response(
        intelligence: IncidentIntelligence,
    ) -> IncidentIntelligenceResponse:
        return IncidentIntelligenceResponse(
            correlations=[
                CorrelationResponse(
                    source_finding=correlation.source_finding,
                    target_finding=correlation.target_finding,
                    type=correlation.type,
                    confidence=correlation.confidence,
                    evidence=correlation.evidence,
                )
                for correlation in intelligence.correlations
            ],
            root_causes=[
                RootCauseCandidateResponse(
                    title=root_cause.title,
                    description=root_cause.description,
                    confidence=root_cause.confidence,
                    supporting_findings=root_cause.supporting_findings,
                    supporting_evidence=root_cause.supporting_evidence,
                )
                for root_cause in intelligence.root_causes
            ],
            recommendations=intelligence.recommendations,
        )
