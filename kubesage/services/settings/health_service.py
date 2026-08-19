import time
from collections.abc import Callable
from datetime import UTC, datetime

from kubesage.ai.factory import create_ai_provider
from kubesage.models.settings_service import SettingsService
from kubesage.models.settings_test import (
    ServiceStatus,
    ServiceTestResponse,
)
from kubesage.services.loki_service import LokiService
from kubesage.services.prometheus_service import PrometheusService
from kubesage.utils.config import settings


class SettingsHealthService:
    def __init__(self) -> None:
        self.prometheus = PrometheusService()
        self.loki = LokiService()
        self.ai = create_ai_provider(settings=settings)

    def test(self, service: SettingsService) -> ServiceTestResponse:
        match service:
            case SettingsService.PROMETHEUS:
                return self._test_prometheus()

            case SettingsService.LOKI:
                return self._test_loki()

            case SettingsService.OPENTELEMETRY:
                return self._test_opentelemetry()

            case SettingsService.AI:
                return self._test_ai()

    def _test_prometheus(self) -> ServiceTestResponse:
        return self._test(self.prometheus.is_available, "Prometheus")

    def _test_loki(self) -> ServiceTestResponse:
        return self._test(self.loki.is_available, "Loki")

    def _test_opentelemetry(self) -> ServiceTestResponse:
        if not settings.otlp_endpoint:
            return self._response(
                ServiceStatus.DISCONNECTED,
                message="OTLP endpoint is not configured",
            )

        return self._response(
            ServiceStatus.CONNECTED,
            message="OTLP endpoint is configured",
        )

    def _test_ai(self) -> ServiceTestResponse:
        return self._test(self.ai.is_server_reachable, "AI")

    def _test(
        self, check: Callable[[], bool], service_name: str
    ) -> ServiceTestResponse:
        start = time.perf_counter()
        available = check()
        latency_ms = round((time.perf_counter() - start) * 1000)

        return self._response(
            ServiceStatus.CONNECTED if available else ServiceStatus.DISCONNECTED,
            latency_ms=latency_ms,
            message=(None if available else f"{service_name} is unreachable"),
        )

    @staticmethod
    def _response(
        status: ServiceStatus,
        *,
        latency_ms: int | None = None,
        message: str | None = None,
    ) -> ServiceTestResponse:
        return ServiceTestResponse(
            status=status,
            checked_at=datetime.now(UTC),
            latency_ms=latency_ms,
            message=message,
        )
