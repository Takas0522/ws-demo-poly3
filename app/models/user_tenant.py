"""User tenant model for managing user-tenant relationships."""
from pydantic import BaseModel, Field, ConfigDict


class UserTenant(BaseModel):
    """
    User tenant model for managing user-tenant relationships.
    
    Attributes:
        id: Unique identifier for the user-tenant assignment
        userId: User identifier (also used as partition key in Cosmos DB)
        tenantId: Tenant identifier
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "usr_123_tenant_priv",
                "userId": "usr_123456789",
                "tenantId": "tnt_privileged",
            }
        }
    )
    
    id: str = Field(..., description="Unique identifier for the user-tenant assignment")
    userId: str = Field(..., description="User identifier")
    tenantId: str = Field(..., description="Tenant identifier")
