import logging

from .context import get_request_id


class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):  # type: ignore[no-untyped-def]
        request_id = get_request_id()

        return (
            f"[{request_id[:8]}] {msg}",
            kwargs,
        )
