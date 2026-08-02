from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kubesage.api.schemas.dashboard import DashboardRecentAnalysis, DashboardSummary
from kubesage.database import FindingModel
from kubesage.database.models.analysis import AnalysisModel
from kubesage.models.finding import Severity


class DashboardRepository:
    """Repository for dashboard data."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_summary(self) -> DashboardSummary:
        """Get the dashboard summary."""

        total_analyses = self.session.scalar(select(func.count(AnalysisModel.id)))
        total_findings = self.session.scalar(select(func.count(FindingModel.id)))
        critical_findings = self.session.scalar(
            select(func.count(FindingModel.id)).where(
                FindingModel.severity == Severity.CRITICAL.value
            )
        )
        high_findings = self.session.scalar(
            select(func.count(FindingModel.id)).where(
                FindingModel.severity == Severity.HIGH.value
            )
        )
        last_analysis_at = self.session.scalar(
            select(func.max(AnalysisModel.created_at))
        )

        return DashboardSummary(
            total_analyses=total_analyses or 0,
            total_findings=total_findings or 0,
            critical_findings=critical_findings or 0,
            high_findings=high_findings or 0,
            last_analysis_at=last_analysis_at,
        )

    def get_recent_analyses(self, limit: int = 5) -> list[DashboardRecentAnalysis]:
        """Get recent analyses."""

        analyses = (
            self.session.execute(
                select(AnalysisModel)
                .order_by(AnalysisModel.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        result = []
        for analysis in analyses:
            severity = None
            if analysis.findings:
                severity = max(
                    analysis.findings,
                    key=lambda finding: Severity(finding.severity).weight,
                ).severity

            result.append(
                DashboardRecentAnalysis(
                    id=analysis.id,
                    namespace=analysis.namespace,
                    pod=analysis.pod,
                    severity=Severity(severity) if severity else Severity.INFO,
                    created_at=analysis.created_at,
                )
            )

        return result
