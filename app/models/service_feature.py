"""Service feature models"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ServiceFeature(BaseModel):
    """ServiceFeature CosmosDB document model"""

    id: str = Field(..., description="機能ID (feature-{service_id}-{連番})")
    type: str = Field(default="service_feature")
    service_id: str = Field(...)
    feature_key: str = Field(...)
    feature_name: str = Field(...)
    description: str = Field(default="")
    default_enabled: bool = Field(default=False)
    created_at: datetime = Field(...)
    updated_at: Optional[datetime] = Field(default=None)
    partitionKey: str = Field(...)  # = service_id

    class Config:
        populate_by_name = True


class TenantServiceFeature(BaseModel):
    """TenantServiceFeature CosmosDB document model"""

    id: str = Field(..., description="{tenant_id}_{feature_id}")
    type: str = Field(default="tenant_service_feature")
    tenant_id: str = Field(...)
    service_id: str = Field(...)
    feature_id: str = Field(...)
    feature_key: str = Field(...)
    is_enabled: bool = Field(...)
    updated_at: datetime = Field(...)
    updated_by: str = Field(...)
    partitionKey: str = Field(...)  # = tenant_id

    class Config:
        populate_by_name = True
