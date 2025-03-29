"""Health check endpoint for monitoring application status."""

import fastapi
from fastapi import APIRouter

from components.core import schemas

router = APIRouter(
    prefix="/health_check",
    tags=["services"],
    responses={200: {"description": "Service is healthy"}},
)


@router.get("/", response_model=schemas.HealthCheck)
async def health_check() -> schemas.HealthCheck:
    """Check the health status of the service."""
    return schemas.HealthCheck(
        service_name="FastAPI Test",
        status="healthy"
    )