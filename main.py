"""Main entry point for the FastAPI application."""

import uvicorn
# Import all models to ensure they're loaded before app creation
import components.user.models
import components.credit.models
import components.payment.models
import components.dictionary.models
import components.plan.models

from restapi.router import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)