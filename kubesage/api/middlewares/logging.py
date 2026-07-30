import time
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from kubesage.observability.tracing import current_trace_context

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
        ctx = current_trace_context()

        log_data = {
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "elapsed": round(elapsed * 1000, 2),
            "trace_id": ctx.trace_id,
            "span_id": ctx.span_id,
        }

        if path in IGNORED_PATHS:
            logger.debug("health_check", **log_data)
        else:
            logger.info("http_request", **log_data)

        return response  # type: ignore[no-any-return]
