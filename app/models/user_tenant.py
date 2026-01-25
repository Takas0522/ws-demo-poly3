"""User tenant model for managing user-tenant relationships."""
from pydantic import BaseModel, Field, ConfigDict


class UserTenant(BaseModel):
    """
    User tenant model for managing user-tenant relationships.
    
    Attributes:
        userId: User identifier
        tenantId: Tenant identifier
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "userId": "usr_123456789",
                "tenantId": "tnt_privileged",
            }
        }
    )
    
    userId: str = Field(..., description="User identifier")
    tenantId: str = Field(..., description="Tenant identifier")
