from openai import Client

from kubesage.ai.enums import AIProviderType
from kubesage.ai.provider import AIProvider
from kubesage.ai.providers.openai_compatible import OpenAICompatibleProvider
from kubesage.utils.config import Settings


def create_ai_provider(settings: Settings) -> AIProvider:
    match settings.ai_provider:
        case AIProviderType.OLLAMA | AIProviderType.OPEN_AI:
            return OpenAICompatibleProvider(
                client=Client(
                    base_url=settings.ai_url,
                    api_key=settings.ai_api_key,
                ),
                model=settings.ai_model,
            )

    raise Exception(f"Unsupported AI provider: {settings.ai_provider}")
