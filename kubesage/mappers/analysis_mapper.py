from uuid import UUID

from kubesage.api.schemas.analysis import (
    AIReportResponse,
    AnalysisResponse,
    EvidenceResponse,
    FindingDetailResponse,
    IncidentResponse,
    ResourceResponse,
)
from kubesage.database.models.analysis import AnalysisModel
from kubesage.database.models.incident_snapshot import IncidentSnapshotModel
from kubesage.mappers.ai_report_mapper import AIReportMapper
from kubesage.mappers.finding_mapper import FindingMapper
from kubesage.mappers.incident_intelligent_mapper import IncidentIntelligentMapper
from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.incident import Incident


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

        return Analysis(
            id=UUID(model.id),
            incident=Incident.model_validate(incident_data),
            findings=[FindingMapper.to_domain(f) for f in model.findings],
            report=(AIReportMapper.to_domain(model.report) if model.report else None),
            duration_ms=model.duration_ms,
            created_at=model.created_at,
            trigger=AnalysisTrigger(model.trigger),
        )

    @staticmethod
    def to_detail_response(analysis: Analysis) -> AnalysisResponse:
        """Convert an Analysis to an AnalysisResponse."""

        findings = sorted(
            analysis.findings,
            key=lambda f: (
                -f.severity.weight,
                -f.priority,
                -f.confidence,
            ),
        )

        return AnalysisResponse(
            id=analysis.id,
            incident=IncidentResponse(
                namespace=analysis.incident.namespace,
                pod=analysis.incident.pod,
                pod_uid=analysis.incident.pod_uid,
                phase=analysis.incident.phase,
            ),
            findings=[
                FindingDetailResponse(
                    rule=f.rule,
                    severity=f.severity,
                    kind=f.kind,
                    title=f.title,
                    description=f.description,
                    resource=(
                        ResourceResponse(**f.resource.model_dump())
                        if f.resource
                        else None
                    ),
                    recommendations=f.recommendations,
                    priority=f.priority,
                    confidence=f.confidence,
                    related_findings=f.related_findings,
                    caused_by=f.caused_by,
                    evidences=[
                        EvidenceResponse(**e.model_dump())
                        for e in f.structured_evidences
                    ],
                )
                for f in findings
            ],
            intelligence=IncidentIntelligentMapper.to_response(analysis.intelligence),
            report=(
                AIReportResponse(**analysis.report.model_dump())
                if analysis.report
                else None
            ),
            created_at=analysis.created_at,
            duration_ms=analysis.duration_ms,
        )
