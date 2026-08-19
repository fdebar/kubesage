from pydantic import BaseModel


class ServiceSettings(BaseModel):
    endpoint: str


class AIProviderSettings(BaseModel):
    provider: str
    endpoint: str
    model: str
    api_key_configured: bool


class SettingsResponse(BaseModel):
    environment: str
    version: str
    observability: dict[str, ServiceSettings]
    ai: AIProviderSettings
