"""User role model for managing user-role-service relationships."""
from pydantic import BaseModel, Field, ConfigDict


class UserRole(BaseModel):
    """
    User role model for managing user-role-service relationships.
    
    Attributes:
        id: Unique identifier for the user-role assignment
        userId: User identifier (also used as partition key in Cosmos DB)
        roleId: Role identifier
        serviceId: Service identifier where the role is applicable
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "usr_123_role_admin",
                "userId": "usr_123456789",
                "roleId": "role_admin",
                "serviceId": "srv_auth",
            }
        }
    )
    
    id: str = Field(..., description="Unique identifier for the user-role assignment")
    userId: str = Field(..., description="User identifier")
    roleId: str = Field(..., description="Role identifier")
    serviceId: str = Field(..., description="Service identifier")
