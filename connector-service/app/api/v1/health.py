"""Health check endpoint — GET /health"""

from fastapi import APIRouter
from app.schemas.connector import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Service health check")
def health_check() -> HealthResponse:
    """Returns service status. Always DEMO mode."""
    return HealthResponse()
