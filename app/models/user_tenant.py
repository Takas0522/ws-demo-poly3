"""User tenant model for managing user-tenant relationships."""
from datetime import datetime, UTC
from pydantic import BaseModel, Field, ConfigDict


class UserTenant(BaseModel):
    """
    User tenant model for managing user-tenant relationships.
    
    Attributes:
        id: Unique identifier for this user-tenant relationship
        userId: User identifier
        tenantId: Tenant identifier
        addedAt: Timestamp when the user was added to the tenant
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ut-001",
                "userId": "user-001",
                "tenantId": "tenant-001",
                "addedAt": "2026-01-01T00:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Unique identifier for this user-tenant relationship")
    userId: str = Field(..., description="User identifier")
    tenantId: str = Field(..., description="Tenant identifier")
    addedAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Timestamp when the user was added to the tenant"
    )
