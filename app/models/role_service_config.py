"""RoleServiceConfig model for managing external service role endpoints."""
from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RoleServiceConfig(BaseModel):
    """
    RoleServiceConfig model for managing external service role endpoints.
    
    Attributes:
        id: Unique configuration identifier
        serviceId: Service identifier
        serviceName: Display name of the service
        roleEndpoint: URL endpoint to fetch roles from the service
        isActive: Whether this service is active for role syncing
        lastSyncAt: Last successful sync timestamp
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "rsc-001",
                "serviceId": "user-management-service",
                "serviceName": "テナント管理サービス",
                "roleEndpoint": "http://user-management-service/api/roles",
                "isActive": True,
                "lastSyncAt": "2026-01-24T10:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Unique configuration identifier")
    serviceId: str = Field(..., description="Service identifier")
    serviceName: str = Field(..., description="Service display name")
    roleEndpoint: str = Field(..., description="Role endpoint URL")
    isActive: bool = Field(default=True, description="Active status")
    lastSyncAt: Optional[datetime] = Field(
        default=None, description="Last sync timestamp"
    )
