from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response, Request
from typing import Callable
from uuid import uuid4


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response  # type: ignore[no-any-return]
