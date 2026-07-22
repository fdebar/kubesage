from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from kubesage.observability.factory import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("KubeSage API starting up...")
    yield
