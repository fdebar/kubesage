from fastapi.responses import JSONResponse
from utils.exceptions import (
    PodNotFoundError,
    KubernetesConnectionError,
    PrometheusQueryError,
    AIAnalysisError,
)
from utils.config import logger
from pydantic import BaseModel


def register_exception_handlers(app):

    @app.exception_handler(PodNotFoundError)
    async def pod_not_found(_, exc):
        logger.warning(str(exc))

        return JSONResponse(
            status_code=404,
            content={
                "error": "Pod not found",
                "detail": str(exc),
            },
        )

    @app.exception_handler(KubernetesConnectionError)
    async def kubernetes_error(_, exc):
        logger.error(str(exc))

        return JSONResponse(
            status_code=503,
            content={
                "error": "Kubernetes unavailable",
                "detail": str(exc),
            },
        )

    @app.exception_handler(PrometheusQueryError)
    async def prometheus_error(_, exc):
        logger.error(str(exc))

        return JSONResponse(
            status_code=503,
            content={
                "error": "Prometheus unavailable",
                "detail": str(exc),
            },
        )

    @app.exception_handler(AIAnalysisError)
    async def ai_error(_, exc):
        logger.exception(exc)

        return JSONResponse(
            status_code=502,
            content={
                "error": "AI analysis failed",
                "detail": str(exc),
            },
        )

    @app.exception_handler(Exception)
    async def unexpected(_, exc):
        logger.exception(exc)

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
            },
        )


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None
