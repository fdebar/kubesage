import time
from datetime import datetime

from kubesage.models.settings_service import SettingsService
from kubesage.models.settings_test import (
    ServiceStatus,
    ServiceTestResponse,
)
from kubesage.services.prometheus_service import PrometheusService


class SettingsHealthService:
    def test(self, service: SettingsService) -> ServiceTestResponse:
        match service:
            case SettingsService.PROMETHEUS:
                return self._test_prometheus()
            case _:
                raise NotImplementedError()

    def _test_prometheus(self) -> ServiceTestResponse:
        start = time.perf_counter()
        available = PrometheusService().is_available()
        latency = round((time.perf_counter() - start) * 1000)

        return ServiceTestResponse(
            status=(
                ServiceStatus.CONNECTED if available else ServiceStatus.DISCONNECTED
            ),
            checked_at=datetime.now(),
            latency_ms=latency,
        )
