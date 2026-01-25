"""Authentication API endpoints."""
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Request/Response models
class LoginRequest(BaseModel):
    """Login request model."""
    loginId: str = Field(..., description="User's login identifier (email or username)")
    password: str = Field(..., description="User's password")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "loginId": "admin@example.com",
                "password": "password123"
            }
        }
    }


class LoginResponse(BaseModel):
    """Login response model."""
    accessToken: str = Field(..., description="JWT access token")
    refreshToken: str = Field(..., description="Refresh token")
    expiresIn: int = Field(..., description="Token expiration time in seconds")
    tokenType: str = Field(default="Bearer", description="Token type")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expiresIn": 3600,
                "tokenType": "Bearer"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: dict = Field(..., description="Error details")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "code": "AUTH002",
                    "message": "認証に失敗しました"
                }
            }
        }
    }


class VerifyRequest(BaseModel):
    """Token verification request model."""
    token: str = Field(..., description="JWT access token to verify")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class VerifyResponse(BaseModel):
    """Token verification response model."""
    userId: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    tenants: list = Field(..., description="Tenant information")
    roles: dict = Field(..., description="Role information")
    isActive: bool = Field(..., description="User active status")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "userId": "user-001",
                "name": "システム管理者",
                "tenants": [
                    {
                        "id": "tenant-001",
                        "name": "特権テナント",
                        "isPrivileged": True
                    }
                ],
                "roles": {
                    "auth-service": ["全体管理者"]
                },
                "isActive": True
            }
        }
    }


class RefreshRequest(BaseModel):
    """Token refresh request model."""
    refreshToken: str = Field(..., description="Refresh token")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class RefreshResponse(BaseModel):
    """Token refresh response model."""
    accessToken: str = Field(..., description="New JWT access token")
    refreshToken: str = Field(..., description="New refresh token")
    expiresIn: int = Field(..., description="Token expiration time in seconds")
    tokenType: str = Field(default="Bearer", description="Token type")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expiresIn": 3600,
                "tokenType": "Bearer"
            }
        }
    }


# Error messages mapping
ERROR_MESSAGES = {
    "AUTH001": "認証情報が提供されていません",
    "AUTH002": "無効なトークンです",
    "AUTH003": "トークンの有効期限が切れています",
    "AUTH006": "特権テナントに所属していないため、ログインできません",
    "AUTH007": "アカウントがロックされています。しばらく経ってから再試行してください",
}


@router.post("/login", response_model=LoginResponse, responses={
    401: {"model": ErrorResponse, "description": "Authentication failed"},
    403: {"model": ErrorResponse, "description": "Access denied"},
    423: {"model": ErrorResponse, "description": "Account locked"}
})
async def login(request: Request, login_request: LoginRequest):
    """
    User login endpoint.
    
    Authenticates user credentials and returns JWT tokens.
    
    - **loginId**: User's login identifier (email or username)
    - **password**: User's password
    
    Returns JWT access token and refresh token on success.
    
    **Security Features**:
    - Password verification using bcrypt (cost=12)
    - JWT generation using RS256 algorithm
    - Login attempt tracking
    - Account locking after 5 failed attempts (30-minute lock)
    - Only privileged tenant users can log in
    """
    from app.services.authentication_service import authentication_service
    
    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"
    
    # Authenticate user
    token_data, error_code = await authentication_service.authenticate(
        login_id=login_request.loginId,
        password=login_request.password,
        ip_address=client_ip
    )
    
    # Handle errors
    if error_code:
        error_message = ERROR_MESSAGES.get(error_code, "認証に失敗しました")
        
        # Determine HTTP status code based on error code
        if error_code == "AUTH007":
            status_code = status.HTTP_423_LOCKED
        elif error_code == "AUTH006":
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message
                }
            }
        )
    
    return token_data


@router.get("/public-key", summary="Get Public Key", description="Retrieve the RSA public key for JWT verification")
async def get_public_key():
    """
    Get RSA public key for JWT verification.
    
    Returns the public key that should be used by other services to verify JWT tokens.
    """
    from app.core.jwt_service import jwt_service
    
    public_key = jwt_service.get_public_key()
    return {"publicKey": public_key}


@router.post("/verify", response_model=VerifyResponse, responses={
    401: {"model": ErrorResponse, "description": "Invalid or expired token"},
    423: {"model": ErrorResponse, "description": "Account locked"}
})
async def verify(verify_request: VerifyRequest):
    """
    JWT token verification endpoint.
    
    Verifies the JWT access token signature, expiration, and user validity.
    
    - **token**: JWT access token to verify
    
    Returns user information on success.
    
    **Error codes**:
    - AUTH001: No authentication info provided
    - AUTH002: Invalid token
    - AUTH003: Token expired
    - AUTH007: Account locked
    """
    from app.services.authentication_service import authentication_service
    
    # Verify token
    user_info, error_code = await authentication_service.verify_access_token(
        token=verify_request.token
    )
    
    # Handle errors
    if error_code:
        error_message = ERROR_MESSAGES.get(error_code, "認証に失敗しました")
        
        # Determine HTTP status code based on error code
        if error_code == "AUTH007":
            status_code = status.HTTP_423_LOCKED
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message
                }
            }
        )
    
    return user_info


@router.post("/refresh", response_model=RefreshResponse, responses={
    401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
    423: {"model": ErrorResponse, "description": "Account locked"}
})
async def refresh(refresh_request: RefreshRequest):
    """
    JWT token refresh endpoint.
    
    Refreshes the access token using a valid refresh token.
    Implements refresh token rotation - old refresh token is invalidated.
    
    - **refreshToken**: Valid refresh token
    
    Returns new access token and refresh token on success.
    
    **Security Features**:
    - Refresh token rotation (old token invalidated)
    - Token reuse detection (revokes all user tokens on reuse)
    - Single use enforcement
    
    **Error codes**:
    - AUTH002: Invalid or revoked token
    - AUTH003: Token expired
    - AUTH007: Account locked
    """
    from app.services.authentication_service import authentication_service
    
    # Refresh tokens
    token_data, error_code = await authentication_service.refresh_tokens(
        refresh_token=refresh_request.refreshToken
    )
    
    # Handle errors
    if error_code:
        error_message = ERROR_MESSAGES.get(error_code, "トークンのリフレッシュに失敗しました")
        
        # Determine HTTP status code based on error code
        if error_code == "AUTH007":
            status_code = status.HTTP_423_LOCKED
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message
                }
            }
        )
    
    return token_data
