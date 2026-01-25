"""Login attempt model for tracking authentication attempts."""
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LoginAttempt(BaseModel):
    """
    Login attempt model for tracking authentication attempts.
    
    Attributes:
        id: Unique identifier for the login attempt
        loginId: Login identifier (email or username) that was used
        isSuccess: Whether the login attempt was successful
        ipAddress: IP address from which the login was attempted
        userAgent: User agent string from the client
        attemptedAt: Timestamp of the login attempt
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "att_123456789",
                "loginId": "admin@example.com",
                "isSuccess": True,
                "ipAddress": "192.168.1.100",
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "attemptedAt": "2024-01-01T12:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Unique identifier for the login attempt")
    loginId: str = Field(..., description="Login identifier (email or username)")
    isSuccess: bool = Field(..., description="Whether the login attempt was successful")
    ipAddress: Optional[str] = Field(default=None, description="IP address of the client")
    userAgent: Optional[str] = Field(default=None, description="User agent string")
    attemptedAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Timestamp of the login attempt"
    )
