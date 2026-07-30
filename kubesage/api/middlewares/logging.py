import time
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

IGNORED_PATHS = {
    "/ready",
    "/health",
    "/live",
    "/metrics",
}


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        path = request.url.path

        log_data = {
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "elapsed": round(elapsed * 1000, 2),
        }

        if path in IGNORED_PATHS:
            logger.debug("health_check", **log_data)
        else:
            logger.info("http_request", **log_data)

        return response  # type: ignore[no-any-return]
