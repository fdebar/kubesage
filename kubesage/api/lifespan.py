from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from opentelemetry import trace

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("kubesage_api_starting_up")

    try:
        yield
    finally:
        logger.info("kubesage_api_shutting_down")

        provider = trace.get_tracer_provider()
        if hasattr(provider, "shutdown"):
            provider.shutdown()
            logger.info("opentelemetry_provider_shutdown_completed")
