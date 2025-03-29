"""Core schemas for the application."""

from pydantic import BaseModel


class HealthCheck(BaseModel):
    """Schema for health check response."""
    service_name: str
    status: str