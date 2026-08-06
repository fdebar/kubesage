import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from kubesage.utils.exceptions import (
    AIAnalysisError,
    KubernetesConnectionError,
    PodNotFoundError,
    PrometheusQueryError,
)

logger = structlog.get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PodNotFoundError)
    async def pod_not_found(request: Request, exc: PodNotFoundError) -> JSONResponse:
        logger.warning(str(exc))

        return JSONResponse(
            status_code=404,
            content={
                "error": "Pod not found",
                "detail": str(exc),
                "request_id": request.state.request_id,
            },
        )

    @app.exception_handler(KubernetesConnectionError)
    async def kubernetes_error(
        request: Request, exc: KubernetesConnectionError
    ) -> JSONResponse:
        logger.error(str(exc))

        return JSONResponse(
            status_code=503,
            content={
                "error": "Kubernetes unavailable",
                "detail": str(exc),
                "request_id": request.state.request_id,
            },
        )

    @app.exception_handler(PrometheusQueryError)
    async def prometheus_error(
        request: Request, exc: PrometheusQueryError
    ) -> JSONResponse:
        logger.error(str(exc))

        return JSONResponse(
            status_code=503,
            content={
                "error": "Prometheus unavailable",
                "detail": str(exc),
                "request_id": request.state.request_id,
            },
        )

    @app.exception_handler(AIAnalysisError)
    async def ai_error(request: Request, exc: AIAnalysisError) -> JSONResponse:
        logger.exception(exc)

        return JSONResponse(
            status_code=502,
            content={
                "error": "AI analysis failed",
                "detail": str(exc),
                "request_id": request.state.request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(exc)

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request.state.request_id,
            },
        )


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None
