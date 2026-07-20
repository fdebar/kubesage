from analyzers.engine import DiagnosticEngine
from services.kubernetes_service import KubernetesService


class IncidentService:

    def __init__(self):

        self.kubernetes = KubernetesService()
        self.engine = DiagnosticEngine()

    def analyze(self, namespace, pod):

        incident = self.kubernetes.collect(namespace, pod)

        findings = self.engine.analyze(incident)

        return incident, findings
