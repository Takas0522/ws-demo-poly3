"""Schemas module initialization."""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    TokenPair,
    UserProfile,
    TenantInfo,
    TokenVerifyResponse,
    CurrentUserResponse,
    SwitchTenantRequest,
    HealthCheckResponse,
    ErrorResponse,
)

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "TokenPair",
    "UserProfile",
    "TenantInfo",
    "TokenVerifyResponse",
    "CurrentUserResponse",
    "SwitchTenantRequest",
    "HealthCheckResponse",
    "ErrorResponse",
]
