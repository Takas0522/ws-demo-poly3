"""User model for authentication."""
from datetime import datetime, UTC
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class UserRole(BaseModel):
    """Embedded user role information."""
    serviceId: str = Field(..., description="Service identifier")
    roleId: str = Field(..., description="Role identifier")
    roleName: str = Field(..., description="Role name")


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
        roles: List of roles assigned to the user (embedded)
        tenantIds: List of tenant IDs the user belongs to (embedded)
        createdAt: Account creation timestamp
        updatedAt: Last update timestamp
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "user-001",
                "loginId": "admin@example.com",
                "name": "システム管理者",
                "passwordHash": "$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",
                "isActive": True,
                "lockedUntil": None,
                "roles": [
                    {
                        "serviceId": "auth-service",
                        "roleId": "role-auth-admin",
                        "roleName": "全体管理者"
                    }
                ],
                "tenantIds": ["tenant-001"],
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
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
    roles: Optional[List[UserRole]] = Field(
        default=None, description="List of roles assigned to the user"
    )
    tenantIds: Optional[List[str]] = Field(
        default=None, description="List of tenant IDs the user belongs to"
    )
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Account creation timestamp"
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )
