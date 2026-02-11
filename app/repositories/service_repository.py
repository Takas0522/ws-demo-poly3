"""Service repository"""
import logging
from typing import List, Optional
from datetime import datetime
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions

from app.config import get_settings
from app.models.service import Service, TenantService

logger = logging.getLogger(__name__)
settings = get_settings()


class ServiceRepository:
    """Service repository for Cosmos DB operations"""

    def __init__(self):
        self.client = None
        self.database = None
        self.services_container = None
        self.tenant_services_container = None

    async def initialize(self):
        """Initialize Cosmos DB client and containers"""
        try:
            self.client = CosmosClient(
                settings.cosmos_db_endpoint,
                settings.cosmos_db_key,
                connection_verify=settings.cosmos_db_connection_verify,
                connection_mode="Gateway",  # エミュレーター用にGatewayモードを使用
                enable_endpoint_discovery=False  # IPリダイレクトを無効化
            )
            self.database = self.client.get_database_client(
                settings.cosmos_db_database)
            self.services_container = self.database.get_container_client(
                "services")
            self.tenant_services_container = self.database.get_container_client(
                "tenant_services")
            logger.info("Service repository initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize service repository: {e}")
            raise

    async def close(self):
        """Close Cosmos DB client"""
        if self.client:
            await self.client.close()

    async def get_all_services(self) -> List[Service]:
        """Get all services"""
        try:
            query = "SELECT * FROM c WHERE c.type = 'service'"
            items = []
            async for item in self.services_container.query_items(
                query=query
            ):
                items.append(Service(**item))
            return items
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            raise

    async def get_service_by_id(self, service_id: str) -> Optional[Service]:
        """Get service by ID"""
        try:
            item = await self.services_container.read_item(
                item=service_id,
                partition_key=service_id
            )
            return Service(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get service {service_id}: {e}")
            raise

    async def get_tenant_services(self, tenant_id: str) -> List[dict]:
        """Get services assigned to a tenant with details"""
        try:
            # Get tenant service assignments
            query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id"
            parameters = [{"name": "@tenant_id", "value": tenant_id}]

            tenant_services = []
            async for item in self.tenant_services_container.query_items(
                query=query,
                parameters=parameters
            ):
                tenant_services.append(TenantService(**item))

            # Get service details
            result = []
            for ts in tenant_services:
                service = await self.get_service_by_id(ts.service_id)
                if service:
                    result.append({
                        "id": service.id,
                        "name": service.name,
                        "assigned_at": ts.assigned_at.isoformat(),
                        "assigned_by": ts.assigned_by
                    })

            return result
        except Exception as e:
            logger.error(f"Failed to get tenant services for {tenant_id}: {e}")
            raise

    async def assign_service_to_tenant(
        self,
        tenant_id: str,
        service_id: str,
        assigned_by: str
    ) -> TenantService:
        """Assign a service to a tenant"""
        try:
            # Check if already assigned
            query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id AND c.service_id = @service_id"
            parameters = [
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@service_id", "value": service_id}
            ]

            async for item in self.tenant_services_container.query_items(
                query=query,
                parameters=parameters
            ):
                # Already assigned
                return TenantService(**item)

            # Create new assignment
            tenant_service = TenantService(
                tenant_id=tenant_id,
                service_id=service_id,
                assigned_at=datetime.utcnow(),
                assigned_by=assigned_by
            )

            # mode='json' で datetime を ISO文字列に変換（Cosmos DB SDK は json.dumps を使用するため）
            item_dict = tenant_service.model_dump(mode='json')
            item_dict["id"] = f"{tenant_id}_{service_id}"
            item_dict["tenantId"] = tenant_id  # パーティションキー用

            await self.tenant_services_container.create_item(body=item_dict)

            logger.info(f"Service {service_id} assigned to tenant {tenant_id}")
            return tenant_service

        except Exception as e:
            logger.error(f"Failed to assign service to tenant: {e}")
            raise

    async def unassign_service_from_tenant(
        self,
        tenant_id: str,
        service_id: str
    ) -> bool:
        """Unassign a service from a tenant"""
        try:
            item_id = f"{tenant_id}_{service_id}"
            await self.tenant_services_container.delete_item(
                item=item_id,
                partition_key=tenant_id
            )
            logger.info(
                f"Service {service_id} unassigned from tenant {tenant_id}")
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Failed to unassign service from tenant: {e}")
            raise


# Global repository instance
service_repository = ServiceRepository()
