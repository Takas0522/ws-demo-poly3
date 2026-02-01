"""認証API"""
from fastapi import APIRouter, Depends, HTTPException, Header
import logging

from app.schemas.auth import LoginRequest, LoginResponse, TokenPayload, LogoutResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.models.user import User
from app.dependencies import (
    get_auth_service,
    get_user_service,
    get_current_user_from_token,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """
    User login
    
    Authenticates user with username/password and issues JWT token.
    
    Args:
        credentials: Login credentials (username and password)
        auth_service: Authentication service (injected)
    
    Returns:
        LoginResponse containing access token and user information
    
    Raises:
        HTTPException: 401 if authentication fails, 403 if account is inactive
    """
    # ユーザー認証
    user = await auth_service.authenticate(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=401, detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    # JWT生成
    token_response = auth_service.create_token(user)

    logger.info(
        "User logged in successfully",
        extra={"user_id": user.id, "tenant_id": user.tenant_id},
    )

    return token_response


@router.post("/verify", response_model=TokenPayload)
async def verify_token(
    authorization: str = Header(..., alias="Authorization"),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenPayload:
    """
    Verify JWT token
    
    This endpoint is used by other services to verify token validity.
    
    Args:
        authorization: Authorization header with Bearer token
        auth_service: Authentication service (injected)
    
    Returns:
        TokenPayload containing decoded token information
    
    Raises:
        HTTPException: 401 if token is invalid or missing Bearer prefix
    """
    BEARER_PREFIX = "Bearer "
    if not authorization.startswith(BEARER_PREFIX):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[len(BEARER_PREFIX):]
    token_data = auth_service.verify_token(token)

    return TokenPayload(
        sub=token_data.user_id,
        username=token_data.username,
        tenant_id=token_data.tenant_id,
        roles=token_data.roles,
        exp=token_data.exp,
        iat=token_data.iat,
        jti=token_data.jti,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: User = Depends(get_current_user_from_token)
) -> LogoutResponse:
    """
    User logout
    
    Note: Phase 1 uses simple implementation. Token invalidation is handled
    client-side. Redis-based blacklist implementation planned for Phase 2.
    
    Args:
        current_user: Currently authenticated user (injected)
    
    Returns:
        LogoutResponse with success message
    """
    logger.info(
        "User logged out successfully",
        extra={"user_id": current_user.id, "tenant_id": current_user.tenant_id},
    )

    return LogoutResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_from_token),
) -> UserResponse:
    """
    Get current user information
    
    Retrieves detailed information about the currently authenticated user.
    
    Args:
        current_user: Currently authenticated user (injected)
    
    Returns:
        UserResponse with current user details
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        displayName=current_user.display_name,
        tenantId=current_user.tenant_id,
        isActive=current_user.is_active,
        createdAt=current_user.created_at,
        updatedAt=current_user.updated_at,
    )
