"""User role model for managing user-role-service relationships."""
from datetime import datetime, UTC
from pydantic import BaseModel, Field, ConfigDict


class UserRole(BaseModel):
    """
    User role model for managing user-role-service relationships.
    
    Attributes:
        id: Unique identifier for this user-role assignment
        userId: User identifier
        roleId: Role identifier
        serviceId: Service identifier where the role is applicable
        assignedAt: Timestamp when the role was assigned
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ur-001",
                "userId": "user-001",
                "roleId": "role-auth-admin",
                "serviceId": "auth-service",
                "assignedAt": "2026-01-01T00:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Unique identifier for this user-role assignment")
    userId: str = Field(..., description="User identifier")
    roleId: str = Field(..., description="Role identifier")
    serviceId: str = Field(..., description="Service identifier")
    assignedAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Timestamp when the role was assigned"
    )
