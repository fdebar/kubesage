from kubesage.models.analysis import Analysis
from kubesage.repositories.analysis_repository import AnalysisRepository
from kubesage.services.incident_service import IncidentService


class AnalysisService:
    def __init__(
        self,
        incident_service: IncidentService,
        repository: AnalysisRepository,
    ) -> None:
        self.incident_service = incident_service
        self.repository = repository

    def analyze(self, namespace: str, pod: str) -> Analysis:
        analysis = self.incident_service.analyze(
            namespace=namespace,
            pod=pod,
        )

        self.repository.save(analysis)

        return analysis
