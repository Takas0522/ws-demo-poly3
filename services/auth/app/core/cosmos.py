from typing import Optional
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from app.core.config import settings


class CosmosDBClient:
    """Cosmos DB client wrapper."""

    def __init__(self):
        self._client: Optional[CosmosClient] = None
        self._database: Optional[DatabaseProxy] = None
        self._container: Optional[ContainerProxy] = None

    def connect(self) -> None:
        """Initialize connection to Cosmos DB."""
        if not settings.cosmos_endpoint or not settings.cosmos_key:
            # Skip connection if credentials are not configured
            return

        try:
            self._client = CosmosClient(settings.cosmos_endpoint, settings.cosmos_key)
            self._database = self._client.get_database_client(settings.cosmos_database_name)
            self._container = self._database.get_container_client(settings.cosmos_container_name)
        except Exception as e:
            # Log the error but don't fail startup - allow the service to run without DB
            print(f"Warning: Failed to connect to Cosmos DB: {e}")
            self._client = None
            self._database = None
            self._container = None

    def disconnect(self) -> None:
        """Close connection to Cosmos DB."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self._container = None

    @property
    def is_connected(self) -> bool:
        """Check if connected to Cosmos DB."""
        return self._client is not None

    @property
    def container(self) -> Optional[ContainerProxy]:
        """Get the container proxy."""
        return self._container


# Global instance
cosmos_client = CosmosDBClient()
