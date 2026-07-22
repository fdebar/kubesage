from prometheus_client import CONTENT_TYPE_LATEST
from fastapi import Response
from fastapi import APIRouter
from prometheus_client import generate_latest


router = APIRouter(
    tags=["Metrics"],
)


@router.get("/metrics", include_in_schema=True)
def metrics() -> Response:
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
