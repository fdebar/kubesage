from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry import trace

from kubesage.observability.factory import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("KubeSage API starting up...")
    try:
        yield
    finally:
        logger.info("KubeSage API shutting down...")

        provider = trace.get_tracer_provider()
        if hasattr(provider, "shutdown"):
            provider.shutdown()
            logger.info("OpenTelemetry provider shutdown completed")
