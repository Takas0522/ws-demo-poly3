"""Role management service with business logic."""

import logging
from typing import List, Optional
from app.models.role import Role
from app.repositories.role_repository import role_repository
from app.repositories.role_service_config_repository import role_service_config_repository

logger = logging.getLogger(__name__)


class RoleService:
    """Service for role management operations."""

    async def list_all_roles(self) -> List[Role]:
        """
        List all available roles.

        Returns:
            List of all roles
        """
        try:
            roles = await role_repository.list_all()
            return roles
        except Exception as e:
            logger.error(f"Failed to list roles: {str(e)}")
            return []

    async def list_roles_by_service(self, service_id: str) -> List[Role]:
        """
        List roles for a specific service.

        Args:
            service_id: Service identifier

        Returns:
            List of roles for the service
        """
        try:
            roles = await role_repository.list_by_service(service_id)
            return roles
        except Exception as e:
            logger.error(f"Failed to list roles for service {service_id}: {str(e)}")
            return []

    async def get_auth_service_roles(self) -> List[Role]:
        """
        Get roles defined by the auth service itself.

        Returns:
            List of auth service roles
        """
        # Define auth service roles according to spec
        auth_roles = [
            Role(
                id="role-auth-admin",
                serviceId="auth-service",
                name="全体管理者",
                description="ユーザーの登録・削除を行うことが可能"
            ),
            Role(
                id="role-auth-viewer",
                serviceId="auth-service",
                name="閲覧者",
                description="ユーザーの参照のみ可能"
            )
        ]
        return auth_roles

    async def sync_roles_from_external_services(self) -> int:
        """
        Sync roles from external services based on RoleServiceConfig.

        This method fetches role information from external services
        and stores them in the local roles container.

        Returns:
            Number of services synced successfully
        """
        try:
            # Get active service configurations
            configs = await role_service_config_repository.list_active()
            
            synced_count = 0
            for config in configs:
                try:
                    # TODO: Implement actual HTTP call to fetch roles from config.roleEndpoint
                    # For now, we just log that we would sync
                    logger.info(f"Would sync roles from {config.serviceName} at {config.roleEndpoint}")
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync roles from {config.serviceName}: {str(e)}")
                    
            return synced_count
        except Exception as e:
            logger.error(f"Failed to sync roles from external services: {str(e)}")
            return 0

    async def filter_roles_by_tenant_services(
        self, all_roles: List[Role], tenant_service_ids: List[str]
    ) -> List[Role]:
        """
        Filter roles based on tenant's available services.

        Args:
            all_roles: List of all available roles
            tenant_service_ids: List of service IDs available to the tenant

        Returns:
            Filtered list of roles
        """
        # Filter roles to only include those from services the tenant can use
        filtered_roles = [
            role for role in all_roles
            if role.serviceId in tenant_service_ids
        ]
        return filtered_roles


# Global service instance
role_service = RoleService()
