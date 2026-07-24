import logging

from .adapter import ContextLoggerAdapter


def get_logger(name: str) -> ContextLoggerAdapter:
    return ContextLoggerAdapter(logging.getLogger(name), {})
