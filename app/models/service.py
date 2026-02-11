"""Service models"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Service(BaseModel):
    """Service model"""
    id: str = Field(..., description="Service UUID")
    name: str = Field(..., description="Service name")
    description: str = Field(..., description="Service description")
    api_url: Optional[str] = Field(
        None, description="API URL for role collection")
    is_active: bool = Field(True, description="Is service active")
    is_mock: bool = Field(False, description="Is mock service")
    created_at: Optional[datetime] = Field(
        None, description="Created timestamp")
    updated_at: Optional[datetime] = Field(
        None, description="Updated timestamp")


class TenantService(BaseModel):
    """Tenant service assignment model"""
    tenant_id: str = Field(..., description="Tenant UUID")
    service_id: str = Field(..., description="Service UUID")
    assigned_at: datetime = Field(..., description="Assignment timestamp")
    assigned_by: str = Field(..., description="User UUID who assigned")
