"""
CosmosDB service for database operations.
"""
from typing import Optional, Dict, Any, List
from azure.cosmos import CosmosClient, ContainerProxy, exceptions
from app.core.config import settings


class CosmosDBService:
    """Service for CosmosDB operations."""
    
    def __init__(self) -> None:
        """Initialize CosmosDB client."""
        self.client = CosmosClient(settings.cosmosdb_endpoint, settings.cosmosdb_key)
        self.database = self.client.get_database_client(settings.cosmosdb_database)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database and containers."""
        if self._initialized:
            return
        
        # Create containers if they don't exist
        await self._create_container_if_not_exists("users", "/tenantId")
        await self._create_container_if_not_exists(
            "refresh-tokens", "/userId", default_ttl=604800  # 7 days
        )
        await self._create_container_if_not_exists(
            "audit-logs", "/tenantId", default_ttl=7776000  # 90 days
        )
        
        self._initialized = True
    
    async def _create_container_if_not_exists(
        self, container_id: str, partition_key: str, default_ttl: Optional[int] = None
    ) -> None:
        """Create a container if it doesn't exist."""
        try:
            self.database.create_container(
                id=container_id,
                partition_key={"paths": [partition_key]},
                default_ttl=default_ttl
            )
        except exceptions.CosmosResourceExistsError:
            pass  # Container already exists
    
    def get_container(self, container_id: str) -> ContainerProxy:
        """Get a container proxy."""
        return self.database.get_container_client(container_id)
    
    def get_users_container(self) -> ContainerProxy:
        """Get users container."""
        return self.get_container("users")
    
    def get_refresh_tokens_container(self) -> ContainerProxy:
        """Get refresh tokens container."""
        return self.get_container("refresh-tokens")
    
    def get_audit_logs_container(self) -> ContainerProxy:
        """Get audit logs container."""
        return self.get_container("audit-logs")
    
    async def find_user_by_email(
        self, email: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find user by email."""
        container = self.get_users_container()
        
        if tenant_id:
            query = "SELECT * FROM c WHERE c.email = @email AND c.tenantId = @tenantId"
            parameters = [
                {"name": "@email", "value": email},
                {"name": "@tenantId", "value": tenant_id}
            ]
        else:
            query = "SELECT * FROM c WHERE c.email = @email"
            parameters = [{"name": "@email", "value": email}]
        
        items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        return items[0] if items else None
    
    async def find_user_by_id(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID."""
        container = self.get_users_container()
        try:
            return container.read_item(item=user_id, partition_key=tenant_id)
        except exceptions.CosmosResourceNotFoundError:
            return None
    
    async def update_user_security(
        self, user_id: str, tenant_id: str, security_updates: Dict[str, Any]
    ) -> None:
        """Update user security settings."""
        container = self.get_users_container()
        user = await self.find_user_by_id(user_id, tenant_id)
        if user:
            user["security"].update(security_updates)
            container.upsert_item(user)
    
    async def store_refresh_token(
        self, token_id: str, user_id: str, tenant_id: str, token: str, expires_at: str
    ) -> None:
        """Store refresh token."""
        container = self.get_refresh_tokens_container()
        token_doc = {
            "id": token_id,
            "userId": user_id,
            "tenantId": tenant_id,
            "tokenId": token_id,
            "token": token,
            "expiresAt": expires_at,
            "createdAt": expires_at  # Will use TTL
        }
        container.create_item(token_doc)
    
    async def validate_refresh_token(self, token_id: str, user_id: str) -> bool:
        """Check if refresh token exists."""
        container = self.get_refresh_tokens_container()
        try:
            container.read_item(item=token_id, partition_key=user_id)
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
    
    async def revoke_refresh_token(self, token_id: str, user_id: str) -> None:
        """Revoke a refresh token."""
        container = self.get_refresh_tokens_container()
        try:
            container.delete_item(item=token_id, partition_key=user_id)
        except exceptions.CosmosResourceNotFoundError:
            pass
    
    async def revoke_all_refresh_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user."""
        container = self.get_refresh_tokens_container()
        query = "SELECT * FROM c WHERE c.userId = @userId"
        parameters = [{"name": "@userId", "value": user_id}]
        
        items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        for item in items:
            try:
                container.delete_item(item=item["id"], partition_key=user_id)
            except exceptions.CosmosResourceNotFoundError:
                pass


# Global instance
cosmos_db = CosmosDBService()
