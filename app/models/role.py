"""Role model for managing service roles."""
from pydantic import BaseModel, Field, ConfigDict


class Role(BaseModel):
    """
    Role model for managing service-specific roles.
    
    Attributes:
        id: Unique role identifier (e.g., role-auth-admin)
        serviceId: Service identifier where the role is defined
        name: Display name of the role
        description: Description of what the role allows
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "role-auth-admin",
                "serviceId": "auth-service",
                "name": "全体管理者",
                "description": "ユーザーの登録・削除を行うことが可能",
            }
        }
    )
    
    id: str = Field(..., description="Unique role identifier")
    serviceId: str = Field(..., description="Service identifier")
    name: str = Field(..., description="Role display name")
    description: str = Field(default="", description="Role description")
