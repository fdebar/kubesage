import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from kubesage.observability.context import set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response  # type: ignore[no-any-return]
