"""ロール割り当てリポジトリ"""
from typing import List, Optional, Tuple
from datetime import datetime
from azure.cosmos.exceptions import CosmosHttpResponseError
from app.models.role_assignment import RoleAssignment
import logging

logger = logging.getLogger(__name__)


class RoleRepository:
    """ロール割り当てデータアクセス層"""

    def __init__(self, container):
        self.container = container
        self.logger = logger

    async def create(self, role_assignment: RoleAssignment) -> RoleAssignment:
        """ロール割り当て作成"""
        try:
            role_dict = role_assignment.model_dump(by_alias=True)
            created = await self.container.create_item(body=role_dict)
            return RoleAssignment(**created)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to create role assignment: {e}")
            raise

    async def get(self, role_assignment_id: str, tenant_id: str) -> Optional[RoleAssignment]:
        """ロール割り当て取得"""
        try:
            item = await self.container.read_item(item=role_assignment_id, partition_key=tenant_id)
            return RoleAssignment(**item)
        except CosmosHttpResponseError as e:
            if e.status_code == 404:
                return None
            self.logger.error(f"Failed to get role assignment: {e}")
            raise

    async def delete(self, role_assignment_id: str, tenant_id: str) -> None:
        """ロール割り当て削除"""
        try:
            await self.container.delete_item(item=role_assignment_id, partition_key=tenant_id)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to delete role assignment: {e}")
            raise

    async def get_by_user_id(self, user_id: str, tenant_id: str) -> List[RoleAssignment]:
        """
        ユーザーIDでロール割り当て一覧取得
        
        Args:
            user_id: ユーザーID
            tenant_id: テナントID（パーティションキー）
        
        Returns:
            List[RoleAssignment]: ロール割り当て一覧
        """
        try:
            query = """
                SELECT * FROM c 
                WHERE c.tenantId = @tenant_id 
                  AND c.type = 'role_assignment' 
                  AND c.userId = @user_id
            """
            parameters = [
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@user_id", "value": user_id},
            ]

            items = self.container.query_items(
                query=query, parameters=parameters, partition_key=tenant_id
            )

            role_assignments = []
            async for item in items:
                role_assignments.append(RoleAssignment(**item))

            return role_assignments
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to get role assignments by user_id: {e}")
            raise

    async def find_by_user_and_service(
        self, user_id: str, tenant_id: str, service_id: str, role_name: str
    ) -> Optional[RoleAssignment]:
        """
        ユーザー、サービス、ロール名で検索（重複チェック用）
        
        Args:
            user_id: ユーザーID
            tenant_id: テナントID
            service_id: サービスID
            role_name: ロール名
        
        Returns:
            Optional[RoleAssignment]: 見つかった場合はRoleAssignment、なければNone
        """
        try:
            query = """
                SELECT * FROM c 
                WHERE c.tenantId = @tenant_id 
                  AND c.type = 'role_assignment' 
                  AND c.userId = @user_id
                  AND c.serviceId = @service_id
                  AND c.roleName = @role_name
            """
            parameters = [
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@user_id", "value": user_id},
                {"name": "@service_id", "value": service_id},
                {"name": "@role_name", "value": role_name},
            ]

            items = self.container.query_items(
                query=query, parameters=parameters, partition_key=tenant_id
            )

            async for item in items:
                return RoleAssignment(**item)

            return None
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to find role assignment: {e}")
            raise

    async def create_if_not_exists(
        self,
        user_id: str,
        tenant_id: str,
        service_id: str,
        role_name: str,
        assigned_by: str,
    ) -> Tuple[RoleAssignment, bool]:
        """
        重複チェック付きでロール割り当てを作成
        
        Args:
            user_id: ユーザーID
            tenant_id: テナントID
            service_id: サービスID
            role_name: ロール名
            assigned_by: 割り当て実行者のユーザーID
        
        Returns:
            Tuple[RoleAssignment, bool]: (RoleAssignment, created)
                - created=Trueなら新規作成、Falseなら既存
        """
        # 1. 先に存在チェック
        existing = await self.find_by_user_and_service(
            user_id, tenant_id, service_id, role_name
        )
        if existing:
            return existing, False

        # 2. 決定的IDを使用して作成
        # IDフォーマット: ra_{user_id}_{service_id}_{role_name}
        # Cosmos DBのidフィールドの一意制約を活用
        deterministic_id = f"ra_{user_id}_{service_id}_{role_name}"
        
        role_assignment = RoleAssignment(
            id=deterministic_id,
            user_id=user_id,
            tenant_id=tenant_id,
            service_id=service_id,
            role_name=role_name,
            assigned_by=assigned_by,
            assigned_at=datetime.utcnow(),
        )

        try:
            await self.create(role_assignment)
            return role_assignment, True
        except CosmosHttpResponseError as e:
            if e.status_code == 409:  # Conflict: ID重複
                # 再度取得して返却
                existing = await self.get(deterministic_id, tenant_id)
                if existing:
                    return existing, False
            raise
