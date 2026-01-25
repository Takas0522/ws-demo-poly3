from typing import Optional, Dict
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from app.core.config import settings


class CosmosDBClient:
    """Cosmos DB client wrapper with support for multiple containers."""

    def __init__(self):
        self._client: Optional[CosmosClient] = None
        self._database: Optional[DatabaseProxy] = None
        self._container: Optional[ContainerProxy] = None
        self._containers: Dict[str, ContainerProxy] = {}

    def connect(self) -> None:
        """Initialize connection to Cosmos DB."""
        if not settings.cosmosdb_endpoint or not settings.cosmosdb_key:
            # Skip connection if credentials are not configured
            return

        try:
            self._client = CosmosClient(settings.cosmosdb_endpoint, settings.cosmosdb_key)
            self._database = self._client.get_database_client(settings.cosmosdb_database)
            self._container = self._database.get_container_client(settings.cosmosdb_container)
            
            # Initialize container proxies for all containers
            self._containers["users"] = self._database.get_container_client("users")
            self._containers["login-attempts"] = self._database.get_container_client("login-attempts")
        except Exception as e:
            # Log the error but don't fail startup - allow the service to run without DB
            print(f"Warning: Failed to connect to Cosmos DB: {e}")
            self._client = None
            self._database = None
            self._container = None
            self._containers = {}

    def disconnect(self) -> None:
        """Close connection to Cosmos DB."""
        if self._client:
            # CosmosClient does not have a close() method in recent versions
            # Just clear the references
            self._client = None
            self._database = None
            self._container = None
            self._containers = {}

    @property
    def is_connected(self) -> bool:
        """Check if connected to Cosmos DB."""
        return self._client is not None

    @property
    def container(self) -> Optional[ContainerProxy]:
        """Get the container proxy (default container for backward compatibility)."""
        return self._container

    def get_container(self, container_name: str) -> Optional[ContainerProxy]:
        """
        Get a specific container by name.
        
        Args:
            container_name: Name of the container (e.g., "users", "login-attempts")
            
        Returns:
            ContainerProxy instance or None if not connected
        """
        return self._containers.get(container_name)

    @property
    def users_container(self) -> Optional[ContainerProxy]:
        """Get the users container."""
        return self._containers.get("users")

    @property
    def login_attempts_container(self) -> Optional[ContainerProxy]:
        """Get the login-attempts container."""
        return self._containers.get("login-attempts")


# Global instance
cosmos_client = CosmosDBClient()
