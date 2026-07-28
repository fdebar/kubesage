import json

import structlog
from openai import OpenAI

from kubesage.models.ai_report import AIReport
from kubesage.utils.config import settings

logger = structlog.get_logger()


class AIService:
    def __init__(self) -> None:
        self.model = settings.openai_model
        self.client = OpenAI(
            base_url=settings.openai_url,
            api_key=settings.openai_api_key,
        )

    def analyze(self, prompt: str) -> AIReport:
        logger.info("llm_start...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Kubernetes SRE."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("llm_analysis_failed", error=str(exc))

            return AIReport(
                summary="AI analysis could not be completed.", root_cause=""
            )

        content = response.choices[0].message.content
        logger.debug("llm_raw_response", content=content)
        try:
            content = json.loads(content or "{}")
            return AIReport(**content)
        except Exception as exc:
            logger.error("llm_invalid_response", error=str(exc))

            return AIReport(summary="AI response validation failed.", root_cause="")
