import structlog

from kubesage.ai.provider import AIProvider
from kubesage.models.ai_report import AIReport

logger = structlog.get_logger()


class AIService:
    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def analyze(self, prompt: str) -> AIReport:
        return self._provider.analyze(prompt)
