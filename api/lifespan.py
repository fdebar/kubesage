from contextlib import asynccontextmanager
from fastapi import FastAPI
from utils.config import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KubeSage API starting up...")
    yield
