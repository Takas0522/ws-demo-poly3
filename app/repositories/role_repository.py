"""Repository for Role data access operations."""

from typing import List, Optional
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from app.models.role import Role
from app.core.cosmos import cosmos_client


class RoleRepository:
    """Repository for Role entity operations."""

    async def find_by_id(self, role_id: str) -> Optional[Role]:
        """
        Find a role by ID.

        Args:
            role_id: Role identifier

        Returns:
            Role instance or None if not found
        """
        container = cosmos_client.roles_container
        if not container:
            return None

        try:
            item = container.read_item(item=role_id, partition_key=role_id)
            return Role(**item)
        except CosmosResourceNotFoundError:
            return None
        except Exception:
            return None

    async def list_all(self) -> List[Role]:
        """
        List all roles.

        Returns:
            List of all roles
        """
        container = cosmos_client.roles_container
        if not container:
            return []

        query = "SELECT * FROM c ORDER BY c.serviceId, c.name"
        
        try:
            items = list(
                container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )
            return [Role(**item) for item in items]
        except Exception:
            return []

    async def list_by_service(self, service_id: str) -> List[Role]:
        """
        List roles for a specific service.

        Args:
            service_id: Service identifier

        Returns:
            List of roles for the service
        """
        container = cosmos_client.roles_container
        if not container:
            return []

        query = "SELECT * FROM c WHERE c.serviceId = @serviceId ORDER BY c.name"
        parameters = [{"name": "@serviceId", "value": service_id}]
        
        try:
            items = list(
                container.query_items(
                    query=query, parameters=parameters, enable_cross_partition_query=True
                )
            )
            return [Role(**item) for item in items]
        except Exception:
            return []

    async def create(self, role: Role) -> Role:
        """
        Create a new role.

        Args:
            role: Role instance to create

        Returns:
            Created Role instance
        """
        container = cosmos_client.roles_container
        if not container:
            raise RuntimeError("Cosmos DB not connected")

        role_dict = role.model_dump(mode="json")
        container.create_item(body=role_dict)
        return role

    async def update(self, role: Role) -> Role:
        """
        Update a role.

        Args:
            role: Role instance to update

        Returns:
            Updated Role instance
        """
        container = cosmos_client.roles_container
        if not container:
            raise RuntimeError("Cosmos DB not connected")

        role_dict = role.model_dump(mode="json")
        container.upsert_item(body=role_dict)
        return role

    async def delete(self, role_id: str) -> bool:
        """
        Delete a role.

        Args:
            role_id: Role identifier

        Returns:
            True if deleted, False otherwise
        """
        container = cosmos_client.roles_container
        if not container:
            return False

        try:
            container.delete_item(item=role_id, partition_key=role_id)
            return True
        except Exception:
            return False


# Global repository instance
role_repository = RoleRepository()
