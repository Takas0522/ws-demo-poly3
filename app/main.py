from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.cosmos import cosmos_client
from app.api import health, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    cosmos_client.connect()
    yield
    # Shutdown
    cosmos_client.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, tags=["authentication"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "message": "Auth Service API",
    }
