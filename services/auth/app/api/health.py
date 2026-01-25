from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.core.cosmos import cosmos_client


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    version: str
    cosmos_db: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Service health status
    """
    cosmos_status = "connected" if cosmos_client.is_connected else "not_configured"

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        cosmos_db=cosmos_status,
    )
