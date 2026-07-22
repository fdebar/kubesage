from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response, Request
from typing import Callable
from kubesage.observability import setup_logging
from kubesage.observability.context import set_request_id
import uuid


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        setup_logging()
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response  # type: ignore[no-any-return]
