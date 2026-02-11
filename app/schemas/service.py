"""Service schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ServiceResponse(BaseModel):
    """Service response schema"""
    id: str
    name: str
    description: str
    api_url: Optional[str] = None
    is_active: bool
    is_mock: bool


class ServiceDetailResponse(ServiceResponse):
    """Service detail response schema"""
    created_at: datetime
    updated_at: Optional[datetime] = None
    roles: Optional[List[dict]] = None


class ServicesListResponse(BaseModel):
    """Services list response schema"""
    data: List[ServiceResponse]


class TenantServiceResponse(BaseModel):
    """Tenant service response schema"""
    id: str
    name: str
    assigned_at: datetime
    assigned_by: str


class TenantServicesResponse(BaseModel):
    """Tenant services response schema"""
    tenant_id: str
    services: List[TenantServiceResponse]


class AssignServiceRequest(BaseModel):
    """Assign service request schema"""
    service_id: str = Field(..., description="Service UUID to assign")


class AssignServiceResponse(BaseModel):
    """Assign service response schema"""
    tenant_id: str
    service_id: str
    assigned_at: datetime
