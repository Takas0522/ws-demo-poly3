"""Service feature service"""
import logging
from datetime import datetime, timezone
from fastapi import HTTPException

from app.repositories.service_feature_repository import ServiceFeatureRepository
from app.models.service_feature import TenantServiceFeature
from app.schemas.service_feature import (
    ServiceFeatureResponse,
    TenantServiceFeatureResponse,
    ServiceFeaturesListResponse,
    TenantServiceFeaturesListResponse,
)
from app.utils.auth import JWTPayload, has_role

logger = logging.getLogger(__name__)


class ServiceFeatureService:
    """Service feature business logic"""

    def __init__(self, repository: ServiceFeatureRepository):
        self.repository = repository

    async def get_service_features(self, service_id: str) -> ServiceFeaturesListResponse:
        """Get features for a service"""
        # Service existence check
        if not await self.repository.service_exists(service_id):
            raise HTTPException(status_code=404, detail="Service not found")

        features = await self.repository.get_features_by_service_id(service_id)
        return ServiceFeaturesListResponse(
            service_id=service_id,
            features=[
                ServiceFeatureResponse(
                    id=f.id,
                    service_id=f.service_id,
                    feature_key=f.feature_key,
                    feature_name=f.feature_name,
                    description=f.description,
                    default_enabled=f.default_enabled,
                    created_at=f.created_at,
                )
                for f in features
            ],
        )

    async def get_tenant_service_features(
        self,
        tenant_id: str,
        service_id: str,
        current_user: JWTPayload,
    ) -> TenantServiceFeaturesListResponse:
        """Get tenant-specific feature settings for a service"""
        # Tenant ID validation (global_admin can access any tenant)
        if current_user.tenant_id != tenant_id and not has_role(current_user, ["global_admin"]):
            raise HTTPException(status_code=403, detail="Forbidden")

        # Service assignment check (global_admin can view any service features)
        if not has_role(current_user, ["global_admin"]):
            tenant_service = await self.repository.get_tenant_service(tenant_id, service_id)
            if tenant_service is None:
                raise HTTPException(
                    status_code=403,
                    detail="Service is not assigned to this tenant",
                )

        # Get master features and tenant settings
        features = await self.repository.get_features_by_service_id(service_id)
        tenant_settings = await self.repository.get_tenant_feature_settings(tenant_id, service_id)

        # Merge
        tenant_map = {ts.feature_id: ts for ts in tenant_settings}
        result = []
        for feature in features:
            tenant_setting = tenant_map.get(feature.id)
            result.append(
                TenantServiceFeatureResponse(
                    feature_id=feature.id,
                    service_id=feature.service_id,
                    feature_key=feature.feature_key,
                    feature_name=feature.feature_name,
                    description=feature.description,
                    is_enabled=tenant_setting.is_enabled if tenant_setting else feature.default_enabled,
                    is_default=tenant_setting is None,
                    updated_at=tenant_setting.updated_at if tenant_setting else None,
                    updated_by=tenant_setting.updated_by if tenant_setting else None,
                )
            )

        return TenantServiceFeaturesListResponse(
            tenant_id=tenant_id,
            service_id=service_id,
            features=result,
        )

    async def update_tenant_service_feature(
        self,
        tenant_id: str,
        service_id: str,
        feature_id: str,
        is_enabled: bool,
        current_user: JWTPayload,
    ) -> TenantServiceFeatureResponse:
        """Update tenant-specific feature setting"""
        # Role validation
        if not has_role(current_user, ["global_admin", "admin"]):
            raise HTTPException(status_code=403, detail="Forbidden")

        # Service assignment check (global_admin can update any service features)
        if not has_role(current_user, ["global_admin"]):
            tenant_service = await self.repository.get_tenant_service(tenant_id, service_id)
            if tenant_service is None:
                raise HTTPException(
                    status_code=403,
                    detail="Service is not assigned to this tenant",
                )

        # Feature existence check
        feature = await self.repository.get_feature_by_id(feature_id, service_id)
        if feature is None:
            raise HTTPException(status_code=404, detail="Feature not found")

        # Create / update tenant feature
        now = datetime.now(timezone.utc)
        tenant_feature = TenantServiceFeature(
            id=f"{tenant_id}_{feature_id}",
            type="tenant_service_feature",
            tenant_id=tenant_id,
            service_id=service_id,
            feature_id=feature_id,
            feature_key=feature.feature_key,
            is_enabled=is_enabled,
            updated_at=now,
            updated_by=current_user.user_id,
            partitionKey=tenant_id,
        )
        await self.repository.upsert_tenant_feature(tenant_feature)

        return TenantServiceFeatureResponse(
            feature_id=feature.id,
            service_id=feature.service_id,
            feature_key=feature.feature_key,
            feature_name=feature.feature_name,
            description=feature.description,
            is_enabled=is_enabled,
            is_default=False,
            updated_at=now,
            updated_by=current_user.user_id,
        )
