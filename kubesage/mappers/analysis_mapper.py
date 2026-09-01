from uuid import UUID

from kubesage.api.schemas.analysis import (
    AIReportResponse,
    AnalysisResponse,
    CorrelationResponse,
    EvidenceResponse,
    FindingDetailResponse,
    IncidentResponse,
    ResourceResponse,
    RootCauseCandidateResponse,
)
from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.incident_snapshot import IncidentSnapshotModel
from kubesage.mappers.ai_report_mapper import AIReportMapper
from kubesage.mappers.finding_mapper import FindingMapper
from kubesage.mappers.incident_intelligence_mapper import (
    IncidentIntelligenceMapper,
)
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import (
    IncidentIntelligence,
)


class AnalysisMapper:
    @staticmethod
    def to_model(analysis: Analysis) -> AnalysisModel:
        """Map an Analysis to an AnalysisModel."""

        model = AnalysisModel(
            id=str(analysis.id),
            namespace=analysis.incident.namespace,
            pod=analysis.incident.pod,
            pod_uid=analysis.incident.pod_uid,
            duration_ms=analysis.duration_ms,
            summary=analysis.report.summary if analysis.report else None,
            highest_severity=(
                analysis.highest_severity.value if analysis.highest_severity else None
            ),
            phase=analysis.incident.phase,
            findings_count=len(analysis.findings),
            created_at=analysis.created_at,
            trigger=analysis.trigger.value,
        )

        model.findings = [
            FindingMapper.to_model(finding, str(analysis.id))
            for finding in analysis.findings
        ]

        model.incident_snapshot = IncidentSnapshotModel(
            analysis_id=str(analysis.id),
            data=analysis.incident.model_dump(mode="json"),
        )

        model.correlations = IncidentIntelligenceMapper.correlations_to_models(
            analysis.intelligence.correlations,
            str(analysis.id),
        )

        model.root_causes = IncidentIntelligenceMapper.root_causes_to_models(
            analysis.intelligence.root_causes,
            str(analysis.id),
        )

        if analysis.report:
            model.report = AIReportMapper.to_model(analysis.report, str(analysis.id))

        return model

    @staticmethod
    def to_domain(model: AnalysisModel) -> Analysis:
        """Convert an AnalysisModel to an Analysis."""

        incident_data = (
            model.incident_snapshot.data
            if model.incident_snapshot is not None
            else {
                "namespace": model.namespace,
                "pod": model.pod,
                "pod_uid": model.pod_uid,
                "phase": model.phase,
                "observed_at": model.created_at,
            }
        )

        findings = [FindingMapper.to_domain(finding) for finding in model.findings]

        return Analysis(
            id=UUID(model.id),
            incident=Incident.model_validate(incident_data),
            findings=findings,
            report=(AIReportMapper.to_domain(model.report) if model.report else None),
            duration_ms=model.duration_ms,
            intelligence=IncidentIntelligence(
                findings=findings,
                timeline=[],
                correlations=IncidentIntelligenceMapper.correlations_to_domain(
                    model.correlations
                ),
                root_causes=IncidentIntelligenceMapper.root_causes_to_domain(
                    model.root_causes
                ),
                recommendations=[],
            ),
            created_at=model.created_at,
            trigger=AnalysisTrigger(model.trigger),
        )

    @staticmethod
    def to_detail_response(analysis: Analysis) -> AnalysisResponse:
        """Convert an Analysis to an AnalysisResponse."""

        findings = sorted(
            analysis.findings,
            key=lambda finding: (
                -finding.severity.weight,
                -finding.priority,
                -finding.confidence,
            ),
        )

        return AnalysisResponse(
            id=analysis.id,
            trigger=analysis.trigger.value,
            incident=IncidentResponse(
                namespace=analysis.incident.namespace,
                pod=analysis.incident.pod,
                pod_uid=analysis.incident.pod_uid,
                phase=analysis.incident.phase,
            ),
            highest_severity=analysis.highest_severity,
            findings_count=len(findings),
            findings=[
                FindingDetailResponse(
                    rule=finding.rule,
                    severity=finding.severity,
                    kind=finding.kind,
                    title=finding.title,
                    description=finding.description,
                    resource=(
                        ResourceResponse(**finding.resource.model_dump())
                        if finding.resource
                        else None
                    ),
                    recommendations=finding.recommendations,
                    priority=finding.priority,
                    confidence=finding.confidence,
                    related_findings=finding.related_findings,
                    caused_by=finding.caused_by,
                    evidences=[
                        EvidenceResponse(**evidence.model_dump())
                        for evidence in finding.structured_evidences
                    ],
                )
                for finding in findings
            ],
            correlations=[
                CorrelationResponse(
                    source_finding=correlation.source_finding,
                    target_finding=correlation.target_finding,
                    type=correlation.type,
                    confidence=correlation.confidence,
                    evidence=correlation.evidence,
                )
                for correlation in analysis.intelligence.correlations
            ],
            root_causes=[
                RootCauseCandidateResponse(
                    finding=root_cause.finding,
                    title=root_cause.title,
                    description=root_cause.description,
                    confidence=root_cause.confidence,
                    supporting_findings=root_cause.supporting_findings,
                    supporting_evidence=root_cause.supporting_evidence,
                )
                for root_cause in analysis.intelligence.root_causes
            ],
            report=(
                AIReportResponse(**analysis.report.model_dump())
                if analysis.report
                else None
            ),
            created_at=analysis.created_at,
            duration_ms=analysis.duration_ms,
        )
