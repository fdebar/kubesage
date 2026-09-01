import json

from kubesage.database.models.analysis_correlation import (
    AnalysisCorrelationModel,
)
from kubesage.database.models.analysis_root_cause import (
    AnalysisRootCauseModel,
)
from kubesage.models.incident_intelligence import (
    Correlation,
    CorrelationType,
    RootCauseCandidate,
)


class IncidentIntelligenceMapper:
    @staticmethod
    def correlations_to_models(
        correlations: list[Correlation],
        analysis_id: str,
    ) -> list[AnalysisCorrelationModel]:
        return [
            AnalysisCorrelationModel(
                analysis_id=analysis_id,
                source_finding=correlation.source_finding,
                target_finding=correlation.target_finding,
                type=correlation.type.value,
                confidence=correlation.confidence,
                evidence=json.dumps(correlation.evidence),
            )
            for correlation in correlations
        ]

    @staticmethod
    def correlations_to_domain(
        models: list[AnalysisCorrelationModel],
    ) -> list[Correlation]:
        return [
            Correlation(
                source_finding=model.source_finding,
                target_finding=model.target_finding,
                type=CorrelationType(model.type),
                confidence=model.confidence,
                evidence=json.loads(model.evidence) if model.evidence else [],
            )
            for model in models
        ]

    @staticmethod
    def root_causes_to_models(
        root_causes: list[RootCauseCandidate],
        analysis_id: str,
    ) -> list[AnalysisRootCauseModel]:
        return [
            AnalysisRootCauseModel(
                analysis_id=analysis_id,
                finding=root_cause.finding,
                title=root_cause.title,
                description=root_cause.description,
                confidence=root_cause.confidence,
                supporting_findings=json.dumps(root_cause.supporting_findings),
                supporting_evidence=json.dumps(root_cause.supporting_evidence),
            )
            for root_cause in root_causes
        ]

    @staticmethod
    def root_causes_to_domain(
        models: list[AnalysisRootCauseModel],
    ) -> list[RootCauseCandidate]:
        return [
            RootCauseCandidate(
                finding=model.finding,
                title=model.title,
                description=model.description,
                confidence=model.confidence,
                supporting_findings=(
                    json.loads(model.supporting_findings)
                    if model.supporting_findings
                    else []
                ),
                supporting_evidence=(
                    json.loads(model.supporting_evidence)
                    if model.supporting_evidence
                    else []
                ),
            )
            for model in models
        ]
