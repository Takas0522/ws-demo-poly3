"""Service feature models"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ServiceFeature(BaseModel):
    """ServiceFeature CosmosDB document model"""
    id: str = Field(..., description="Feature ID (feature-{service_id}-{sequence})")
    type: str = Field(default="service_feature")
    service_id: str = Field(..., description="Associated service ID")
    feature_key: str = Field(..., description="Machine-readable feature key")
    feature_name: str = Field(..., description="Display name")
    description: str = Field(default="", description="Feature description")
    default_enabled: bool = Field(default=False, description="Default enabled state")
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp")
    partitionKey: str = Field(..., description="Partition key (= service_id)")

    class Config:
        populate_by_name = True


class TenantServiceFeature(BaseModel):
    """TenantServiceFeature CosmosDB document model"""
    id: str = Field(..., description="{tenant_id}_{feature_id}")
    type: str = Field(default="tenant_service_feature")
    tenant_id: str = Field(..., description="Tenant ID")
    service_id: str = Field(..., description="Service ID")
    feature_id: str = Field(..., description="ServiceFeature.id reference")
    feature_key: str = Field(..., description="Feature key (redundant for lookup)")
    is_enabled: bool = Field(..., description="Enabled state for tenant")
    updated_at: datetime = Field(..., description="Last updated timestamp")
    updated_by: str = Field(..., description="User ID of updater")
    partitionKey: str = Field(..., description="Partition key (= tenant_id)")

    class Config:
        populate_by_name = True
