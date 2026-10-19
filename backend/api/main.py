from fastapi import FastAPI

from backend.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Callrizer backend is running",
        "docs": "/docs",
    }