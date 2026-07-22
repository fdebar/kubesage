from fastapi import FastAPI
from api.lifespan import lifespan
from api.routers.system import router as system_router
from api.routers.analysis import router as analysis_router
from api.routers.metrics import router as metrics_router
from api.exception_handlers import register_exception_handlers
from api.middlewares.request_id import RequestIDMiddleware
from api.middlewares.logging import LoggingMiddleware
from api.middlewares.metrics import MetricsMiddleware
from observability.factory import get_logger

get_logger(__name__)

app = FastAPI(
    title="KubeSage",
    description="AI-powered Kubernetes Incident Analysis",
    version="0.8.0",
    lifespan=lifespan,
)

app.include_router(system_router)
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(metrics_router)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)

register_exception_handlers(app)
