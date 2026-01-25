"""Refresh token model for token rotation."""
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RefreshToken(BaseModel):
    """
    Refresh token model for storing and validating refresh tokens.
    
    Attributes:
        id: Unique token identifier (also used as partition key in Cosmos DB)
        userId: User ID this token belongs to
        tokenHash: Hashed refresh token value
        isRevoked: Whether this token has been revoked
        expiresAt: Token expiration timestamp
        createdAt: Token creation timestamp
        usedAt: Timestamp when token was last used (for rotation)
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "rt-550e8400-e29b-41d4-a716-446655440000",
                "userId": "user-001",
                "tokenHash": "$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",
                "isRevoked": False,
                "expiresAt": "2026-02-01T00:00:00Z",
                "createdAt": "2026-01-25T00:00:00Z",
                "usedAt": None,
            }
        }
    )
    
    id: str = Field(..., description="Unique token identifier")
    userId: str = Field(..., description="User ID this token belongs to")
    tokenHash: str = Field(..., description="Hashed refresh token value")
    isRevoked: bool = Field(default=False, description="Whether this token has been revoked")
    expiresAt: datetime = Field(..., description="Token expiration timestamp")
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Token creation timestamp"
    )
    usedAt: Optional[datetime] = Field(
        default=None, description="Timestamp when token was last used"
    )
