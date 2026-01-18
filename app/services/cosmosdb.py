"""
CosmosDB service for database operations.
"""
import os
from typing import Optional, Dict, Any, List
from azure.cosmos import CosmosClient, ContainerProxy, exceptions
from app.core.config import settings

# SSL証明書検証を無効化（開発環境のCosmosDBエミュレータ用）
os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'


class CosmosDBService:
    """Service for CosmosDB operations."""

    def __init__(self) -> None:
        """Initialize CosmosDB client."""
        self.client: Optional[CosmosClient] = None
        self.database = None
        self._initialized = False
        self._connection_attempted = False

    async def initialize(self) -> None:
        """Initialize database and containers."""
        if self._initialized:
            return

        if not self._connection_attempted:
            self._connection_attempted = True
            try:
                print(f"  Connecting to: {settings.cosmosdb_endpoint}")
                print(f"  Database: {settings.cosmosdb_database}")

                # CosmosDBエミュレータの場合はSSL証明書の検証を無効化
                self.client = CosmosClient(
                    settings.cosmosdb_endpoint,
                    settings.cosmosdb_key,
                    connection_verify=False  # SSL検証を無効化
                )
                self.database = self.client.get_database_client(
                    settings.cosmosdb_database)
                print("  ✓ Connection established")
            except Exception as e:
                print(f"  ✗ Connection failed: {e}")
                return

        if not self.client or not self.database:
            return

        # DevContainerのinit-cosmosdb.shで既にコンテナは作成済み
        # 既存のコンテナを確認するだけ
        print("  Checking existing containers...")
        try:
            containers = ["Users", "refresh-tokens", "audit-logs"]
            for container_name in containers:
                try:
                    self.database.get_container_client(container_name).read()
                    print(f"    ✓ Container '{container_name}' is available")
                except exceptions.CosmosResourceNotFoundError:
                    print(
                        f"    ⚠ Container '{container_name}' not found - may need to run init-cosmosdb.sh")
        except Exception as e:
            print(f"  ⚠ Could not verify containers: {e}")

        self._initialized = True

    def get_container(self, container_id: str) -> Optional[ContainerProxy]:
        """Get a container proxy."""
        if not self.database:
            return None
        return self.database.get_container_client(container_id)

    def get_users_container(self) -> ContainerProxy:
        """Get users container."""
        return self.get_container("Users")

    def get_refresh_tokens_container(self) -> ContainerProxy:
        """Get refresh tokens container."""
        return self.get_container("refresh-tokens")

    def get_audit_logs_container(self) -> ContainerProxy:
        """Get audit logs container."""
        return self.get_container("audit-logs")

    def get_tenant_users_container(self) -> ContainerProxy:
        """Get tenant-users container."""
        return self.get_container("TenantUsers")

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

        items = list(container.query_items(
            query=query, parameters=parameters, enable_cross_partition_query=True))
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

        items = list(container.query_items(
            query=query, parameters=parameters, enable_cross_partition_query=True))
        for item in items:
            try:
                container.delete_item(item=item["id"], partition_key=user_id)
            except exceptions.CosmosResourceNotFoundError:
                pass

    async def get_user_tenants(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tenants that a user belongs to."""
        container = self.get_tenant_users_container()
        query = "SELECT * FROM c WHERE c.userId = @userId"
        parameters = [{"name": "@userId", "value": user_id}]

        items = list(container.query_items(
            query=query, parameters=parameters, enable_cross_partition_query=True))
        return items

    async def get_tenant_user(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific tenant-user relationship."""
        container = self.get_tenant_users_container()
        query = "SELECT * FROM c WHERE c.userId = @userId AND c.tenantId = @tenantId"
        parameters = [
            {"name": "@userId", "value": user_id},
            {"name": "@tenantId", "value": tenant_id}
        ]

        items = list(container.query_items(
            query=query, parameters=parameters, enable_cross_partition_query=True))
        return items[0] if items else None


# Global instance
cosmos_db = CosmosDBService()
