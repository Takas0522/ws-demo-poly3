"""
Pydantic schemas for request/response models.
"""
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    tenant_id: Optional[str] = None
    remember_me: bool = False


class TokenPair(BaseModel):
    """JWT token pair schema."""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"


class TenantInfo(BaseModel):
    """Tenant information schema."""
    id: str
    name: str
    roles: List[str]


class UserProfile(BaseModel):
    """User profile schema."""
    id: str
    email: str
    display_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: str


class LoginResponse(BaseModel):
    """Login response schema."""
    tokens: TokenPair
    user: UserProfile
    tenants: List[TenantInfo] = []


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""
    tokens: TokenPair


class LogoutRequest(BaseModel):
    """Logout request schema."""
    refresh_token: Optional[str] = None
    all_devices: bool = False


class TokenVerifyResponse(BaseModel):
    """Token verification response."""
    valid: bool
    user: Optional[dict] = None


class CurrentUserResponse(BaseModel):
    """Current user response schema."""
    id: str
    email: str
    display_name: str
    tenant_id: str
    roles: List[str]
    permissions: List[str]
    tenants: List[TenantInfo] = []
    selected_tenant_id: Optional[str] = None


class SwitchTenantRequest(BaseModel):
    """Tenant switch request schema."""
    tenant_id: str


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    version: str
    timestamp: str
    uptime: float


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: bool = True
    message: str
    code: str
    status_code: int = 400
