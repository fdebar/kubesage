from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response, Request
from typing import Callable
from utils.config import logger
import time


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        logger.info(
            "%s %s -> %s (%.3fs)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )

        return response  # type: ignore[no-any-return]
