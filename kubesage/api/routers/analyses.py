from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from kubesage.api.dependencies import get_analysis_repository
from kubesage.api.schemas.analysis import (
    AIReportResponse,
    AnalysisResponse,
    EvidenceResponse,
    FindingDetailResponse,
    IncidentResponse,
    ResourceResponse,
)
from kubesage.mappers.analysis_mapper import AnalysisMapper
from kubesage.repositories.analysis_repository import AnalysisRepository

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: UUID,
    repository: AnalysisRepository = Depends(
        get_analysis_repository,
    ),
) -> AnalysisResponse:
    analysis = repository.get(analysis_id)

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    return AnalysisMapper.to_detail_response(analysis)


@router.get("", response_model=list[AnalysisResponse])
def list_analyses(
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> list[AnalysisResponse] | None:
    analyses = repository.list_recent()
    if not analyses:
        return None

    return [
        AnalysisResponse(
            id=analysis.id,
            incident=IncidentResponse(
                namespace=analysis.incident.namespace,
                pod=analysis.incident.pod,
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
                for f in analysis.findings
            ],
            report=(
                AIReportResponse(**analysis.report.model_dump())
                if analysis.report
                else None
            ),
            created_at=analysis.created_at,
            duration_ms=analysis.duration_ms,
        )
        for analysis in analyses
    ]
