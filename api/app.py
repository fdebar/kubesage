from fastapi import FastAPI

from api.lifespan import lifespan
from api.routes import router

app = FastAPI(
    title="KubeSage",
    description="AI-powered Kubernetes Incident Analysis",
    version="0.8.0",
    lifespan=lifespan,
)

app.include_router(router)
