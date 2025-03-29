"""Application configuration and router setup."""

import fastapi
from fastapi.middleware import cors
from fastapi.openapi.utils import get_openapi

from components.core import init_db
from restapi.endpoints import health_check, user, auth, plan

def create_app() -> fastapi.FastAPI:
    """Create and configure the FastAPI application."""
    app = fastapi.FastAPI(
        title="FastAPI Test",
        description="FastAPI Test Application",
        version="1.0.0",
    )

    # Initialize database
    init_db.init_db(app)

    # Add CORS middleware
    app.add_middleware(
        cors.CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_check.router)
    app.include_router(auth.router)
    app.include_router(user.router)
    app.include_router(plan.router)

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="FastAPI Test",
            version="1.0.0",
            description="FastAPI Test Application",
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    return app