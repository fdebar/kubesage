from analyzers.engine import DiagnosticEngine
from services.kubernetes_service import KubernetesService
from services.ai_service import AIService
from utils.prompt_builder import build_prompt


class IncidentService:

    def __init__(self):

        self.kubernetes = KubernetesService()
        self.engine = DiagnosticEngine()
        self.ai = AIService()

    def analyze(
        self,
        namespace,
        pod,
    ):

        incident = self.kubernetes.collect(namespace, pod)

        findings = self.engine.analyze(incident)

        with open("prompts/sre_analysis.txt") as f:

            template = f.read()

        prompt = build_prompt(incident, findings, template)

        report = self.ai.analyze(prompt)

        return report
