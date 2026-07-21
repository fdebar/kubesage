from utils.config import logger
from utils.exceptions import KubeSageException
import json
from openai import OpenAI
from utils.config import settings


class AIService:
    def __init__(self) -> None:
        self.model = settings.openai_model

        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    def analyze(self, prompt: str) -> dict:
        logger.info("Calling LLM....")

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
            KubeSageException.throw_and_exit(
                f"A problem occured while contacting the LLM. Details: {e}"
            )

        content = response.choices[0].message.content

        return json.loads(content or "{}")  # type: ignore
