import time

import structlog
from openai import APIConnectionError, APIStatusError, Client

from kubesage.models.ai_report import AIReport
from kubesage.observability.metrics import (
    LLM_DURATION,
    LLM_REQUESTS,
    LLM_TOKENS,
)

logger = structlog.get_logger()


class OpenAICompatibleProvider:
    def __init__(self, client: Client, model: str) -> None:
        self._client = client
        self._model = model

    def analyze(self, prompt: str) -> AIReport:
        logger.info("ollama_start", model=self._model)

        try:
            start = time.perf_counter()
            response = self._client.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": "You are an expert Kubernetes SRE."},
                    {"role": "user", "content": prompt},
                ],
                response_format=AIReport,
            )
            LLM_DURATION.observe(time.perf_counter() - start)
            LLM_REQUESTS.labels(status="success").inc()
            if response.usage:
                LLM_TOKENS.observe(response.usage.total_tokens)

        except Exception as exc:  # noqa: BLE001
            logger.error("ollama_response_failed", reason=repr(exc))
            LLM_REQUESTS.labels(status="error").inc()

            return AIReport(summary="AI analysis could not be completed.")
        logger.debug("ollama_response_raw", response=response)

        report: AIReport | None = response.choices[0].message.parsed
        if report is None:
            logger.error("ollama_response_empty")

            return AIReport(summary="AI analysis could not be completed.")

        return report

    def is_server_reachable(self) -> bool:
        """Return True if the OpenAI API is reachable and responding."""

        try:
            self._client.models.list(timeout=2.0)
            return True
        except APIConnectionError:
            return False
        except APIStatusError:
            return True
