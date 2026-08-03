from kubesage.api.schemas.dashboard import (
    ClusterStatus,
    DashboardAnalysisItem,
    DashboardMetrics,
    DashboardOverviewResponse,
    SeveritySummary,
)
from kubesage.models.finding import Severity
from kubesage.repositories.analysis_repository import AnalysisRepository
from kubesage.services.kubernetes_service import KubernetesService


class DashboardService:
    def __init__(
        self,
        repository: AnalysisRepository,
        kubernetes_service: KubernetesService,
    ):
        self.repository = repository
        self.kubernetes_service = kubernetes_service

    def overview(self) -> DashboardOverviewResponse:
        analyses = self.repository.list_recent(limit=10) or []

        severities = SeveritySummary(
            critical=self.repository.count_findings_by_severity(Severity.CRITICAL),
            high=self.repository.count_findings_by_severity(Severity.HIGH),
            warning=self.repository.count_findings_by_severity(Severity.WARNING),
            low=self.repository.count_findings_by_severity(Severity.LOW),
            info=self.repository.count_findings_by_severity(Severity.INFO),
        )

        findings = self.repository.count_findings()
        health_score = self._health_score(severities)
        pods = self.kubernetes_service.count_pods()
        nodes = self.kubernetes_service.count_nodes()
        cluster = self.kubernetes_service.get_cluster_info()

        recent = [
            DashboardAnalysisItem(
                id=str(a.id),
                namespace=a.incident.namespace,
                pod=a.incident.pod,
                severity=a.highest_severity,
                created_at=a.created_at,
                duration_ms=a.duration_ms,
            )
            for a in analyses
        ]

        return DashboardOverviewResponse(
            cluster=ClusterStatus(
                name=cluster.name,
                version=cluster.kubernetes_version,
                status=self._cluster_status(health_score),
            ),
            metrics=DashboardMetrics(
                pods=pods,
                nodes=nodes,
                analyses=self.repository.count(),
                findings=findings,
                health_score=health_score,
            ),
            severities=severities,
            recent_analyses=recent,
        )

    def _health_score(self, severity: SeveritySummary) -> int:
        score = 100

        score -= severity.critical * 20
        score -= severity.high * 10
        score -= severity.warning * 5

        return max(score, 0)

    def _cluster_status(self, score: int) -> str:
        if score >= 90:
            return "healthy"

        if score >= 60:
            return "warning"

        return "critical"
