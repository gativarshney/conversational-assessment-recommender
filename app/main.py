from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging

# Set up logging configuration
setup_logging()

# Initialize the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Conversational SHL Assessment Recommender API",
    version="1.0.0"
)

# Mount the router containing the endpoints GET /health and POST /chat
app.include_router(router)
