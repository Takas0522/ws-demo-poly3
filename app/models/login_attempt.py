"""Login attempt model for tracking authentication attempts."""
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LoginAttempt(BaseModel):
    """
    Login attempt model for tracking authentication attempts.
    
    Attributes:
        id: Unique identifier for the login attempt
        userId: User identifier (if user was identified)
        loginId: Login identifier (email or username) that was used
        isSuccess: Whether the login attempt was successful
        ipAddress: IP address from which the login was attempted
        attemptedAt: Timestamp of the login attempt
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "la-001",
                "userId": "user-001",
                "loginId": "admin@example.com",
                "isSuccess": False,
                "ipAddress": "192.168.1.1",
                "attemptedAt": "2026-01-24T09:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Unique identifier for the login attempt")
    userId: Optional[str] = Field(default=None, description="User identifier (if user was identified)")
    loginId: str = Field(..., description="Login identifier (email or username)")
    isSuccess: bool = Field(..., description="Whether the login attempt was successful")
    ipAddress: str = Field(..., description="IP address of the client")
    attemptedAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Timestamp of the login attempt"
    )
