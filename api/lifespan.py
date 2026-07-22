from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from utils.config import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("KubeSage API starting up...")
    yield
