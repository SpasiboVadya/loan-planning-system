"""Core classes and mixins for DB connections"""

from contextlib import asynccontextmanager
from typing import Any, Optional, cast
from typing import Callable, AsyncContextManager

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from components.core import config

settings = config.get_settings()
Base = declarative_base()
SessionMaker = Callable[[], AsyncContextManager[AsyncSession]]


class DatabaseManager:
    def __init__(self, engine: Optional[AsyncEngine] = None) -> None:
        """Initialize DatabaseManager with optional engine for testing."""
        self.engine = engine or self._create_engine()

    def _create_engine(self) -> AsyncEngine:
        """Create async engine for MySQL connection."""
        return create_async_engine(
            settings.async_db_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,  # Enable connection health checks
            pool_size=5,  # Connection pool size
            max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
        )
    
    def get_session(self) -> SessionMaker:
        """Returns SessionMaker for database sessions."""
        if not self.engine:
            raise ValueError("Database engine wasn't initialized")
    
        return cast(
            SessionMaker,
            sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            ),
        )

    @asynccontextmanager
    async def get_db(self) -> AsyncContextManager[AsyncSession]:
        """Get database session context manager."""
        async_session = self.get_session()
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()
