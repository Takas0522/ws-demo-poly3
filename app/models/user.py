"""User model for authentication."""
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class User(BaseModel):
    """
    User model for storing authentication information.
    
    Attributes:
        id: Unique user identifier (also used as partition key in Cosmos DB)
        loginId: Login identifier (email or username)
        name: User's display name
        passwordHash: Hashed password
        isActive: Whether the user account is active
        lockedUntil: Timestamp until which the account is locked (None if not locked)
        createdAt: Account creation timestamp
        updatedAt: Last update timestamp
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "usr_123456789",
                "loginId": "admin@example.com",
                "name": "System Administrator",
                "passwordHash": "$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",
                "isActive": True,
                "lockedUntil": None,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Unique user identifier")
    loginId: str = Field(..., description="Login identifier (email or username)")
    name: str = Field(..., description="User's display name")
    passwordHash: str = Field(..., description="Hashed password")
    isActive: bool = Field(default=True, description="Whether the user account is active")
    lockedUntil: Optional[datetime] = Field(
        default=None, description="Timestamp until which the account is locked"
    )
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Account creation timestamp"
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )
