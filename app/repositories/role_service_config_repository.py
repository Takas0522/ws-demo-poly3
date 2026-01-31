"""Repository for RoleServiceConfig data access operations."""

from typing import List, Optional
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from app.models.role_service_config import RoleServiceConfig
from app.core.cosmos import cosmos_client


class RoleServiceConfigRepository:
    """Repository for RoleServiceConfig entity operations."""

    async def find_by_id(self, config_id: str) -> Optional[RoleServiceConfig]:
        """
        Find a role service config by ID.

        Args:
            config_id: Config identifier

        Returns:
            RoleServiceConfig instance or None if not found
        """
        container = cosmos_client.role_configs_container
        if not container:
            return None

        try:
            item = container.read_item(item=config_id, partition_key=config_id)
            return RoleServiceConfig(**item)
        except CosmosResourceNotFoundError:
            return None
        except Exception:
            return None

    async def find_by_service_id(self, service_id: str) -> Optional[RoleServiceConfig]:
        """
        Find a role service config by service ID.

        Args:
            service_id: Service identifier

        Returns:
            RoleServiceConfig instance or None if not found
        """
        container = cosmos_client.role_configs_container
        if not container:
            return None

        query = "SELECT * FROM c WHERE c.serviceId = @serviceId"
        parameters = [{"name": "@serviceId", "value": service_id}]
        
        try:
            items = list(
                container.query_items(
                    query=query, parameters=parameters, enable_cross_partition_query=True
                )
            )
            if items:
                return RoleServiceConfig(**items[0])
            return None
        except Exception:
            return None

    async def list_all(self) -> List[RoleServiceConfig]:
        """
        List all role service configs.

        Returns:
            List of all configs
        """
        container = cosmos_client.role_configs_container
        if not container:
            return []

        query = "SELECT * FROM c ORDER BY c.serviceName"
        
        try:
            items = list(
                container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )
            return [RoleServiceConfig(**item) for item in items]
        except Exception:
            return []

    async def list_active(self) -> List[RoleServiceConfig]:
        """
        List active role service configs.

        Returns:
            List of active configs
        """
        container = cosmos_client.role_configs_container
        if not container:
            return []

        query = "SELECT * FROM c WHERE c.isActive = true ORDER BY c.serviceName"
        
        try:
            items = list(
                container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )
            return [RoleServiceConfig(**item) for item in items]
        except Exception:
            return []

    async def create(self, config: RoleServiceConfig) -> RoleServiceConfig:
        """
        Create a new role service config.

        Args:
            config: RoleServiceConfig instance to create

        Returns:
            Created RoleServiceConfig instance
        """
        container = cosmos_client.role_configs_container
        if not container:
            raise RuntimeError("Cosmos DB not connected")

        config_dict = config.model_dump(mode="json")
        container.create_item(body=config_dict)
        return config

    async def update(self, config: RoleServiceConfig) -> RoleServiceConfig:
        """
        Update a role service config.

        Args:
            config: RoleServiceConfig instance to update

        Returns:
            Updated RoleServiceConfig instance
        """
        container = cosmos_client.role_configs_container
        if not container:
            raise RuntimeError("Cosmos DB not connected")

        config_dict = config.model_dump(mode="json")
        container.upsert_item(body=config_dict)
        return config


# Global repository instance
role_service_config_repository = RoleServiceConfigRepository()
