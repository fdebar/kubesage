from contextvars import ContextVar

request_id_ctx = ContextVar("request_id", default="unknown")


def set_request_id(request_id: str) -> None:
    request_id_ctx.set(request_id)


def get_request_id() -> str:
    return request_id_ctx.get()
