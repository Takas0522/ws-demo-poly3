"""Service feature schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ServiceFeatureResponse(BaseModel):
    """Service feature master API response"""
    id: str
    service_id: str
    feature_key: str
    feature_name: str
    description: str
    default_enabled: bool
    created_at: datetime


class TenantServiceFeatureResponse(BaseModel):
    """Tenant service feature API response (merged with master)"""
    feature_id: str
    service_id: str
    feature_key: str
    feature_name: str
    description: str
    is_enabled: bool
    is_default: bool
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class UpdateTenantServiceFeatureRequest(BaseModel):
    """Update tenant service feature request"""
    is_enabled: bool


class ServiceFeaturesListResponse(BaseModel):
    """Service features list response"""
    service_id: str
    features: List[ServiceFeatureResponse]


class TenantServiceFeaturesListResponse(BaseModel):
    """Tenant service features list response"""
    tenant_id: str
    service_id: str
    features: List[TenantServiceFeatureResponse]
