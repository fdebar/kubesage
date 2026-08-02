from fastapi import FastAPI

from kubesage.api.exception_handlers import register_exception_handlers
from kubesage.api.lifespan import lifespan
from kubesage.api.middlewares.logging import LoggingMiddleware
from kubesage.api.middlewares.metrics import MetricsMiddleware
from kubesage.api.middlewares.request_id import RequestIDMiddleware
from kubesage.api.routers.analysis import router as analysis_router
from kubesage.api.routers.dashboard import router as dashboard_router
from kubesage.api.routers.metrics import router as metrics_router
from kubesage.api.routers.system import router as system_router
from kubesage.observability.telemetry import setup_telemetry
from kubesage.utils.config import settings

app = FastAPI(
    title=settings.app_name,
    description="AI-powered Kubernetes Incident Analysis",
    version=settings.app_version,
    lifespan=lifespan,
)

setup_telemetry(app)

app.include_router(system_router)
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(metrics_router)

app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

register_exception_handlers(app)
