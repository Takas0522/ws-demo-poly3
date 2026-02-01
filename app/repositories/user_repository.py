"""ユーザーリポジトリ"""
from typing import Optional, List
from azure.cosmos.exceptions import CosmosHttpResponseError
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """ユーザーデータアクセス層"""

    def __init__(self, container):
        self.container = container
        self.logger = logger

    async def create(self, user: User) -> User:
        """ユーザー作成"""
        try:
            user_dict = user.model_dump(by_alias=True)
            created = await self.container.create_item(body=user_dict)
            return User(**created)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to create user: {e}")
            raise

    async def get(self, user_id: str, tenant_id: str) -> Optional[User]:
        """ユーザー取得"""
        try:
            item = await self.container.read_item(item=user_id, partition_key=tenant_id)
            return User(**item)
        except CosmosHttpResponseError as e:
            if e.status_code == 404:
                return None
            self.logger.error(f"Failed to get user: {e}")
            raise

    async def update(self, user_id: str, tenant_id: str, data: dict) -> User:
        """ユーザー更新"""
        try:
            # 既存ユーザー取得
            existing = await self.get(user_id, tenant_id)
            if not existing:
                raise ValueError(f"User {user_id} not found")

            # データマージ
            updated_data = existing.model_dump(by_alias=True)
            for key, value in data.items():
                if value is not None:
                    # キャメルケースに変換
                    if key == "display_name":
                        updated_data["displayName"] = value
                    elif key == "is_active":
                        updated_data["isActive"] = value
                    else:
                        updated_data[key] = value

            # 更新日時を設定
            from datetime import datetime
            updated_data["updatedAt"] = datetime.utcnow().isoformat() + "Z"

            # 保存
            updated = await self.container.upsert_item(body=updated_data)
            return User(**updated)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to update user: {e}")
            raise

    async def delete(self, user_id: str, tenant_id: str) -> None:
        """ユーザー削除"""
        try:
            await self.container.delete_item(item=user_id, partition_key=tenant_id)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to delete user: {e}")
            raise

    async def find_by_username(
        self, username: str, allow_cross_partition: bool = True
    ) -> Optional[User]:
        """
        ユーザー名でユーザー検索
        
        Note: ログイン時はテナントIDが不明なため、クロスパーティションクエリを許可
        """
        try:
            query = """
                SELECT * FROM c 
                WHERE c.type = 'user' 
                  AND c.username = @username
            """
            parameters = [{"name": "@username", "value": username}]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=allow_cross_partition,
            )

            async for item in items:
                return User(**item)

            return None
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to find user by username: {e}")
            raise

    async def find_by_email(
        self, tenant_id: str, email: str
    ) -> Optional[User]:
        """メールアドレスでユーザー検索（テナント内）"""
        try:
            query = """
                SELECT * FROM c 
                WHERE c.tenantId = @tenant_id 
                  AND c.type = 'user' 
                  AND c.email = @email
            """
            parameters = [
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@email", "value": email},
            ]

            items = self.container.query_items(
                query=query, parameters=parameters, partition_key=tenant_id
            )

            async for item in items:
                return User(**item)

            return None
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to find user by email: {e}")
            raise

    async def list_by_tenant(
        self, tenant_id: str, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """テナント内のユーザー一覧取得"""
        try:
            query = """
                SELECT * FROM c 
                WHERE c.tenantId = @tenant_id 
                  AND c.type = 'user'
                ORDER BY c.createdAt DESC
                OFFSET @skip LIMIT @limit
            """
            parameters = [
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@skip", "value": skip},
                {"name": "@limit", "value": limit},
            ]

            items = self.container.query_items(
                query=query, parameters=parameters, partition_key=tenant_id
            )

            users = []
            async for item in items:
                users.append(User(**item))

            return users
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to list users: {e}")
            raise
