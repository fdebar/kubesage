from typing import Protocol

from kubesage.models.ai_report import AIReport


class AIProvider(Protocol):
    def analyze(self, prompt: str) -> AIReport: ...

    def is_server_reachable(self) -> bool: ...
