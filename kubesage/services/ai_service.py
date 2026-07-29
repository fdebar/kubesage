import json
import time

import structlog
from openai import OpenAI

from kubesage.api.metrics import (
    OPENAI_DURATION,
    OPENAI_REQUESTS,
    OPENAI_TOKENS,
)
from kubesage.models.ai_report import AIReport
from kubesage.utils.config import settings

logger = structlog.get_logger()


class AIService:
    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=settings.openai_url,
            api_key=settings.openai_api_key,
        )

    def analyze(self, prompt: str) -> AIReport:
        logger.info("llm_analyze_start...")

        try:
            start = time.perf_counter()
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert Kubernetes SRE."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            OPENAI_DURATION.observe(time.perf_counter() - start)
            OPENAI_REQUESTS.labels(status="success").inc()
            if response.usage:
                OPENAI_TOKENS.observe(response.usage.total_tokens)

        except Exception as exc:  # noqa: BLE001
            logger.error("llm_analyze_failed", error=str(exc))
            OPENAI_REQUESTS.labels(status="error").inc()

            return AIReport(
                summary="AI analysis could not be completed.", root_cause=""
            )
        content = response.choices[0].message.content

        logger.debug("llm_analyze_raw_response", content=content)
        try:
            content = json.loads(content or "{}")
            return AIReport(**content)
        except Exception as exc:
            logger.error("llm_analyze_raw_response_failed", error=str(exc))

            return AIReport(summary="AI response validation failed.", root_cause="")
