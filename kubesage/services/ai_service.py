import time

import structlog
from openai import OpenAI

from kubesage.models.ai_report import AIReport
from kubesage.observability.metrics import (
    OPENAI_DURATION,
    OPENAI_REQUESTS,
    OPENAI_TOKENS,
)
from kubesage.utils.config import settings

logger = structlog.get_logger()


class AIService:
    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=settings.openai_url,
            api_key=settings.openai_api_key,
        )

    def analyze(self, prompt: str) -> AIReport:
        logger.info("llm.analyze.start", model=settings.openai_model)

        try:
            start = time.perf_counter()
            response = self.client.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert Kubernetes SRE."},
                    {"role": "user", "content": prompt},
                ],
                response_format=AIReport,
            )
            OPENAI_DURATION.observe(time.perf_counter() - start)
            OPENAI_REQUESTS.labels(status="success").inc()
            if response.usage:
                OPENAI_TOKENS.observe(response.usage.total_tokens)

        except Exception as exc:  # noqa: BLE001
            logger.error("llm.analyze.response.failed", reason=repr(exc))
            OPENAI_REQUESTS.labels(status="error").inc()

            return AIReport(summary="AI analysis could not be completed.")
        logger.debug("llm.analyze.response.raw", response=response)

        report: AIReport | None = response.choices[0].message.parsed
        if report is None:
            logger.error("llm.analyze.response.empty")

            return AIReport(summary="AI analysis could not be completed.")

        return report
