"""API module initialization."""
from app.api.auth import router as auth_router
from app.api.root import router as root_router

__all__ = ["auth_router", "root_router"]
