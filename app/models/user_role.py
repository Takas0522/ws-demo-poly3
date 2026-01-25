"""User role model for managing user-role-service relationships."""
from pydantic import BaseModel, Field, ConfigDict


class UserRole(BaseModel):
    """
    User role model for managing user-role-service relationships.
    
    Attributes:
        userId: User identifier
        roleId: Role identifier
        serviceId: Service identifier where the role is applicable
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "userId": "usr_123456789",
                "roleId": "role_admin",
                "serviceId": "srv_auth",
            }
        }
    )
    
    userId: str = Field(..., description="User identifier")
    roleId: str = Field(..., description="Role identifier")
    serviceId: str = Field(..., description="Service identifier")
