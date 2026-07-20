from models.report import Report
from analyzers.rules import analyze_incident
from models.incident import Incident
from services.kubernetes_service import KubernetesService


class IncidentService:

    def __init__(self):

        self.kubernetes = KubernetesService()

    def analyze(
        self,
        namespace: str,
        pod: str,
    ) -> tuple[Incident, list[str]]:

        incident = self.kubernetes.collect(
            namespace,
            pod,
        )

        findings = analyze_incident(
            incident
        )

        return Report(
            severity="critical",
            summary="CrashLoopBackOff détecté.",
            findings=findings,
        )
