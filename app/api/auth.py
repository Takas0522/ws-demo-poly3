"""
Authentication API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    TokenVerifyResponse,
    CurrentUserResponse,
    SwitchTenantRequest,
    TenantInfo,
)
from app.services import auth_service
from app.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate user and return JWT tokens.
    
    - **email**: User email address
    - **password**: User password
    - **tenant_id**: Optional tenant ID for multi-tenant scenarios
    - **remember_me**: Extended session flag (not yet implemented)
    """
    return await auth_service.login(request)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest) -> RefreshTokenResponse:
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    """
    tokens = await auth_service.refresh_token(request.refresh_token)
    return RefreshTokenResponse(tokens=tokens)


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Logout user by revoking refresh tokens.
    
    - **refresh_token**: Optional refresh token to revoke
    - **all_devices**: Set to true to logout from all devices
    """
    await auth_service.logout(
        current_user["sub"],
        request.refresh_token,
        request.all_devices
    )
    return {"success": True, "message": "Logged out successfully"}


@router.get("/verify", response_model=TokenVerifyResponse)
async def verify_token(current_user: dict = Depends(get_current_user)) -> TokenVerifyResponse:
    """
    Verify current access token.
    
    Returns the decoded token payload if valid.
    """
    return TokenVerifyResponse(valid=True, user=current_user)


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
) -> CurrentUserResponse:
    """
    Get current user information from token.
    
    Returns user details extracted from the JWT token, including tenants list.
    """
    # Extract tenants from token
    tenants_data = current_user.get("tenants", [])
    tenants = [
        TenantInfo(
            id=t.get("id", ""),
            name=t.get("name", ""),
            roles=t.get("roles", [])
        )
        for t in tenants_data
    ]
    
    return CurrentUserResponse(
        id=current_user["sub"],
        email=current_user["email"],
        display_name=current_user["displayName"],
        tenant_id=current_user["tenantId"],
        roles=current_user.get("roles", []),
        permissions=current_user.get("permissions", []),
        tenants=tenants,
        selected_tenant_id=current_user.get("selectedTenantId"),
    )


@router.post("/switch-tenant")
async def switch_tenant(
    request: SwitchTenantRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Switch user's active tenant.
    
    - **tenant_id**: The ID of the tenant to switch to
    
    Returns a new access token with the updated selectedTenantId.
    """
    tokens = await auth_service.switch_tenant(
        current_user["sub"],
        request.tenant_id,
        current_user
    )
    return {
        "access_token": tokens.access_token,
        "expires_in": tokens.expires_in,
        "token_type": tokens.token_type
    }
