"""
Health check and root endpoints.
"""
import time
from datetime import datetime
from fastapi import APIRouter
from app.schemas import HealthCheckResponse

router = APIRouter(tags=["health"])

# Track start time for uptime calculation
start_time = time.time()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint.
    
    Returns service status, version, and uptime information.
    """
    return HealthCheckResponse(
        status="healthy",
        service="auth-service",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        uptime=time.time() - start_time
    )


@router.get("/")
async def root() -> dict:
    """
    Root endpoint.
    
    Returns basic service information and available endpoints.
    """
    return {
        "service": "SaaS Auth Service (FastAPI)",
        "version": "1.0.0",
        "description": "JWT Authentication Service with tenant-aware authentication",
        "endpoints": {
            "health": "GET /health",
            "login": "POST /auth/login",
            "logout": "POST /auth/logout",
            "refresh": "POST /auth/refresh",
            "verify": "GET /auth/verify",
            "me": "GET /auth/me",
            "docs": "GET /docs",
        }
    }
