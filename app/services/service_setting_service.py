"""Service setting service"""
import logging
from typing import List, Optional
from fastapi import HTTPException

from app.models.service import Service, TenantService
from app.repositories.service_repository import ServiceRepository
from app.utils.auth import JWTPayload, has_role

logger = logging.getLogger(__name__)


class ServiceSettingService:
    """Service setting business logic"""

    def __init__(self, repository: ServiceRepository):
        self.repository = repository

    async def get_all_services(self) -> List[Service]:
        """Get all services"""
        return await self.repository.get_all_services()

    async def get_service_by_id(self, service_id: str) -> Service:
        """Get service by ID"""
        service = await self.repository.get_service_by_id(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service

    async def get_tenant_services(self, tenant_id: str) -> List[dict]:
        """Get services assigned to a tenant"""
        return await self.repository.get_tenant_services(tenant_id)

    async def assign_service_to_tenant(
        self,
        tenant_id: str,
        service_id: str,
        current_user: JWTPayload
    ) -> TenantService:
        """Assign a service to a tenant"""
        # Permission check: Only global_admin
        if not has_role(current_user, ["global_admin"]):
            raise HTTPException(
                status_code=403,
                detail="Only global admin can assign services to tenants"
            )

        # Verify service exists
        service = await self.repository.get_service_by_id(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        # Verify service is active
        if not service.is_active:
            raise HTTPException(status_code=400, detail="Service is not active")

        # Assign service
        try:
            return await self.repository.assign_service_to_tenant(
                tenant_id=tenant_id,
                service_id=service_id,
                assigned_by=current_user.user_id
            )
        except Exception as e:
            logger.error(f"Failed to assign service: {e}")
            raise HTTPException(status_code=500, detail="Failed to assign service")

    async def unassign_service_from_tenant(
        self,
        tenant_id: str,
        service_id: str,
        current_user: JWTPayload
    ) -> bool:
        """Unassign a service from a tenant"""
        # Permission check: Only global_admin
        if not has_role(current_user, ["global_admin"]):
            raise HTTPException(
                status_code=403,
                detail="Only global admin can unassign services from tenants"
            )

        # Unassign service
        success = await self.repository.unassign_service_from_tenant(
            tenant_id=tenant_id,
            service_id=service_id
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Service assignment not found"
            )

        return True
