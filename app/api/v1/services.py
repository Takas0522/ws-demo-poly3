"""Service API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.service import (
    ServicesListResponse,
    ServiceDetailResponse,
    TenantServicesResponse,
    AssignServiceRequest,
    AssignServiceResponse,
    ServiceResponse,
    TenantServiceResponse
)
from app.schemas.service_feature import (
    ServiceFeaturesListResponse,
    TenantServiceFeaturesListResponse,
    TenantServiceFeatureResponse,
    UpdateTenantServiceFeatureRequest,
)
from app.services.service_setting_service import ServiceSettingService
from app.services.service_feature_service import ServiceFeatureService
from app.repositories.service_repository import service_repository
from app.repositories.service_feature_repository import service_feature_repository
from app.utils.dependencies import get_current_user
from app.utils.auth import JWTPayload

router = APIRouter(prefix="/api/v1")

# Service instances
service_setting_service = ServiceSettingService(service_repository)
service_feature_service = ServiceFeatureService(service_feature_repository)


@router.get("/services", response_model=ServicesListResponse)
async def get_services(
    current_user: JWTPayload = Depends(get_current_user)
):
    """Get all services"""
    services = await service_setting_service.get_all_services()
    return ServicesListResponse(
        data=[
            ServiceResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                api_url=s.api_url,
                is_active=s.is_active,
                is_mock=s.is_mock
            )
            for s in services
        ]
    )


@router.get("/services/{service_id}", response_model=ServiceDetailResponse)
async def get_service(
    service_id: str,
    current_user: JWTPayload = Depends(get_current_user)
):
    """Get service by ID"""
    service = await service_setting_service.get_service_by_id(service_id)
    return ServiceDetailResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        api_url=service.api_url,
        is_active=service.is_active,
        is_mock=service.is_mock,
        created_at=service.created_at,
        updated_at=service.updated_at,
        roles=None  # TODO: Implement role collection
    )


@router.get("/tenants/{tenant_id}/services", response_model=TenantServicesResponse)
async def get_tenant_services(
    tenant_id: str,
    current_user: JWTPayload = Depends(get_current_user)
):
    """Get services assigned to a tenant"""
    services = await service_setting_service.get_tenant_services(tenant_id)
    return TenantServicesResponse(
        tenant_id=tenant_id,
        services=[
            TenantServiceResponse(
                id=s["id"],
                name=s["name"],
                assigned_at=s["assigned_at"],
                assigned_by=s["assigned_by"]
            )
            for s in services
        ]
    )


@router.post(
    "/tenants/{tenant_id}/services",
    response_model=AssignServiceResponse,
    status_code=status.HTTP_201_CREATED
)
async def assign_service_to_tenant(
    tenant_id: str,
    request: AssignServiceRequest,
    current_user: JWTPayload = Depends(get_current_user)
):
    """Assign a service to a tenant"""
    tenant_service = await service_setting_service.assign_service_to_tenant(
        tenant_id=tenant_id,
        service_id=request.service_id,
        current_user=current_user
    )
    return AssignServiceResponse(
        tenant_id=tenant_service.tenant_id,
        service_id=tenant_service.service_id,
        assigned_at=tenant_service.assigned_at
    )


@router.delete(
    "/tenants/{tenant_id}/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def unassign_service_from_tenant(
    tenant_id: str,
    service_id: str,
    current_user: JWTPayload = Depends(get_current_user)
):
    """Unassign a service from a tenant"""
    await service_setting_service.unassign_service_from_tenant(
        tenant_id=tenant_id,
        service_id=service_id,
        current_user=current_user
    )


@router.get("/services/{service_id}/features", response_model=ServiceFeaturesListResponse)
async def get_service_features(
    service_id: str,
    current_user: JWTPayload = Depends(get_current_user)
):
    """Get features for a service"""
    return await service_feature_service.get_service_features(service_id)


@router.get("/tenants/{tenant_id}/services/{service_id}/features", response_model=TenantServiceFeaturesListResponse)
async def get_tenant_service_features(
    tenant_id: str,
    service_id: str,
    current_user: JWTPayload = Depends(get_current_user)
):
    """Get tenant-specific feature settings for a service"""
    return await service_feature_service.get_tenant_service_features(
        tenant_id=tenant_id,
        service_id=service_id,
        current_user=current_user
    )


@router.put("/tenants/{tenant_id}/services/{service_id}/features/{feature_id}", response_model=TenantServiceFeatureResponse)
async def update_tenant_service_feature(
    tenant_id: str,
    service_id: str,
    feature_id: str,
    request: UpdateTenantServiceFeatureRequest,
    current_user: JWTPayload = Depends(get_current_user)
):
    """Update tenant-specific feature setting"""
    return await service_feature_service.update_tenant_service_feature(
        tenant_id=tenant_id,
        service_id=service_id,
        feature_id=feature_id,
        is_enabled=request.is_enabled,
        current_user=current_user
    )
