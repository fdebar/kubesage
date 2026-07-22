from fastapi import APIRouter

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
    return {
        "status": "healthy",
        "components": {
            "kubernetes": "up",
            "prometheus": "up",
            "openai": "up",
        },
        "version": "0.8.0",
    }


@router.get("/ready")
def readiness() -> dict[str, bool]:
    return {"ready": True}


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": "0.8.0"}
