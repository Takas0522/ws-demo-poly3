"""Service feature repository"""
import logging
from typing import List, Optional
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions

from app.config import get_settings
from app.models.service_feature import ServiceFeature, TenantServiceFeature

logger = logging.getLogger(__name__)
settings = get_settings()


class ServiceFeatureRepository:
    """Service feature repository for Cosmos DB operations"""

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
                connection_mode="Gateway",
                enable_endpoint_discovery=False
            )
            self.database = self.client.get_database_client(
                settings.cosmos_db_database)
            self.services_container = self.database.get_container_client(
                "services")
            self.tenant_services_container = self.database.get_container_client(
                "tenant_services")
            logger.info("Service feature repository initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize service feature repository: {e}")
            raise

    async def close(self):
        """Close Cosmos DB client"""
        if self.client:
            await self.client.close()

    async def service_exists(self, service_id: str) -> bool:
        """Check if a service exists in the services container"""
        try:
            await self.services_container.read_item(
                item=service_id,
                partition_key=service_id
            )
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(
                f"Failed to check service existence {service_id}: {e}")
            raise

    async def get_features_by_service_id(self, service_id: str) -> List[ServiceFeature]:
        """Get all features for a service"""
        try:
            query = "SELECT * FROM c WHERE c.type = 'service_feature' AND c.service_id = @serviceId"
            parameters = [{"name": "@serviceId", "value": service_id}]
            items = []
            async for item in self.services_container.query_items(
                query=query,
                parameters=parameters,
            ):
                items.append(ServiceFeature(**item))
            return items
        except Exception as e:
            logger.error(
                f"Failed to get features for service {service_id}: {e}")
            raise

    async def get_feature_by_id(self, feature_id: str, service_id: str) -> Optional[ServiceFeature]:
        """Get a feature by ID"""
        try:
            item = await self.services_container.read_item(
                item=feature_id,
                partition_key=feature_id
            )
            return ServiceFeature(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get feature {feature_id}: {e}")
            raise

    async def get_tenant_feature_settings(self, tenant_id: str, service_id: str) -> List[TenantServiceFeature]:
        """Get tenant feature settings for a service"""
        try:
            query = (
                "SELECT * FROM c WHERE c.type = 'tenant_service_feature' "
                "AND c.tenant_id = @tenantId AND c.service_id = @serviceId"
            )
            parameters = [
                {"name": "@tenantId", "value": tenant_id},
                {"name": "@serviceId", "value": service_id}
            ]
            items = []
            async for item in self.tenant_services_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=tenant_id
            ):
                items.append(TenantServiceFeature(**item))
            return items
        except Exception as e:
            logger.error(
                f"Failed to get tenant feature settings for tenant {tenant_id}, service {service_id}: {e}")
            raise

    async def upsert_tenant_feature(self, tenant_feature: TenantServiceFeature) -> TenantServiceFeature:
        """Upsert a tenant feature setting"""
        try:
            item_dict = tenant_feature.model_dump(mode='json')
            item_dict["tenantId"] = tenant_feature.tenant_id

            await self.tenant_services_container.upsert_item(body=item_dict)
            logger.info(f"Tenant feature upserted: {tenant_feature.id}")
            return tenant_feature
        except Exception as e:
            logger.error(
                f"Failed to upsert tenant feature {tenant_feature.id}: {e}")
            raise

    async def get_tenant_service(self, tenant_id: str, service_id: str) -> Optional[dict]:
        """Get tenant service assignment"""
        try:
            query = (
                "SELECT * FROM c WHERE c.type = 'tenant_service' "
                "AND c.tenant_id = @tenantId AND c.service_id = @serviceId"
            )
            parameters = [
                {"name": "@tenantId", "value": tenant_id},
                {"name": "@serviceId", "value": service_id}
            ]
            async for item in self.tenant_services_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=tenant_id
            ):
                return item
            return None
        except Exception as e:
            logger.error(
                f"Failed to get tenant service for tenant {tenant_id}, service {service_id}: {e}")
            raise


# Global repository instance
service_feature_repository = ServiceFeatureRepository()
