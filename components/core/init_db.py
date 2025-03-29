"""Database initialization and dependency injection."""

from typing import AsyncGenerator

import fastapi
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from components.core.database import DatabaseManager
# Import all models to ensure they're registered
import components.user.models
import components.credit.models
import components.payment.models
import components.dictionary.models
import components.plan.models

# Create a single instance of DatabaseManager
db_manager = DatabaseManager()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting database sessions."""
    async with db_manager.get_db() as session:
        yield session

def init_db(app: fastapi.FastAPI) -> None:
    """Initialize database connection."""
    # Add database session dependency to the app
    app.dependency_overrides[AsyncSession] = get_db 