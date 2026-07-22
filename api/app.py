from typing import Callable
from fastapi import FastAPI, Request, Response
from api.lifespan import lifespan
from api.routers.system import router as system_router
from api.routers.analysis import router as analysis_router
from api.exception_handlers import register_exception_handlers
from utils.config import logger
from api.middlewares.request_id import RequestIDMiddleware
import time

app = FastAPI(
    title="KubeSage",
    description="AI-powered Kubernetes Incident Analysis",
    version="0.8.0",
    lifespan=lifespan,
)

app.include_router(system_router)

app.include_router(
    analysis_router,
    prefix="/api/v1",
)

app.add_middleware(RequestIDMiddleware)

register_exception_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    logger.info(
        "%s %s -> %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )

    return response  # type: ignore[no-any-return]
