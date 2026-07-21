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
def health() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": "0.8.0"}
