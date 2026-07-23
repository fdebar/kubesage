import json
import structlog
from openai import OpenAI
from kubesage.utils.config import settings

logger = structlog.get_logger()


class AIService:
    def __init__(self) -> None:
        self.model = settings.openai_model
        self.client = OpenAI(
            base_url=settings.openai_url,
            api_key=settings.openai_api_key,
        )

    def analyze(self, prompt: str) -> dict:
        logger.info("calling_llm....")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Kubernetes SRE."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.error("llm_analysis_failed: %s", e)
            return {
                "summary": "AI analysis could not be completed.",
                "severity": "Unknown",
                "root_cause": "",
                "recommendations": [],
                "kubectl_commands": [],
            }

        content = response.choices[0].message.content

        return json.loads(content or "{}")  # type: ignore
