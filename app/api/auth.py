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


# Error messages mapping
ERROR_MESSAGES = {
    "AUTH002": "認証に失敗しました",
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
