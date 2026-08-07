from fastapi import APIRouter

from kubesage.ai.factory import create_ai_provider
from kubesage.utils.config import settings

router = APIRouter(tags=["System"])


@router.get("/")
def root() -> dict[str, str]:
    return {
        "service": "KubeSage",
        "version": "0.8.0",
        "status": "running",
    }


@router.get("/health")
def health() -> dict[str, str | dict[str, str]]:
    provider = create_ai_provider(settings=settings)

    return {
        "status": "healthy",
        "components": {
            "ai": "up" if provider.is_server_reachable() else "down",
            "kubernetes": "up",
            "prometheus": "up",
        },
        "version": "0.8.0",
    }


@router.get("/ready")
def readiness() -> dict[str, bool]:
    return {"ready": True}


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": "0.8.0"}
