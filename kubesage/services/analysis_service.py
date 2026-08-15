import time
from uuid import UUID

from opentelemetry import trace

from kubesage.models.analysis import Analysis, AnalysisTrigger
from kubesage.models.analysis_summary import AnalysisSummary
from kubesage.observability.metrics import ANALYSIS_DURATION, ANALYSIS_TOTAL
from kubesage.repositories.analysis_repository import AnalysisRepository
from kubesage.services.incident_service import IncidentService

tracer = trace.get_tracer(__name__)


class AnalysisService:
    def __init__(
        self,
        incident_service: IncidentService,
        repository: AnalysisRepository,
    ) -> None:
        self.incident_service = incident_service
        self.repository = repository

    def analyze(self, namespace: str, pod: str, trigger: AnalysisTrigger) -> Analysis:
        start = time.perf_counter()

        with tracer.start_as_current_span("analysis.execute") as span:
            span.set_attribute("analysis.trigger", trigger.value)
            span.set_attribute("k8s.namespace", namespace)
            span.set_attribute("k8s.pod.name", pod)

            try:
                analysis = self.incident_service.analyze(namespace, pod, trigger)
                self.repository.save(analysis)

                ANALYSIS_TOTAL.labels(status="success").inc()

                return analysis

            except Exception as exc:  # noqa: BLE001
                span.record_exception(exc)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))

                ANALYSIS_TOTAL.labels(status="error").inc()

                raise

            finally:
                ANALYSIS_DURATION.observe(time.perf_counter() - start)

    def get(self, analysis_id: UUID) -> Analysis | None:
        return self.repository.get(analysis_id)

    def list_analyses(self, limit: int = 20, offset: int = 0) -> list[Analysis]:
        return self.repository.list_analyses(limit=limit, offset=offset)

    def list_summaries(self, limit: int = 20, offset: int = 0) -> list[AnalysisSummary]:
        return self.repository.list_summaries(limit=limit, offset=offset)

    def count(self) -> int:
        return self.repository.count()
