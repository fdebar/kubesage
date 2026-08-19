from fastapi import APIRouter

from kubesage.models.settings import (
    AIProviderSettings,
    ServiceSettings,
    SettingsResponse,
)
from kubesage.utils.config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
def get_settings() -> SettingsResponse:
    """
    Get settings.

    Returns:
        SettingsResponse: Settings.
    """

    return SettingsResponse(
        environment=settings.environment,
        version=settings.app_version,
        observability={
            "prometheus": ServiceSettings(endpoint=settings.prometheus_url),
            "loki": ServiceSettings(endpoint=settings.loki_url),
            "opentelemetry": ServiceSettings(endpoint=settings.otlp_endpoint or ""),
        },
        ai=AIProviderSettings(
            provider=settings.ai_provider,
            endpoint=settings.ai_url,
            model=settings.ai_model,
            api_key_configured=bool(settings.ai_api_key),
        ),
    )
