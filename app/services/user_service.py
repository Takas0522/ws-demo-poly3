"""ユーザーサービス"""
from typing import List, Optional
from datetime import datetime
import logging

from app.models.user import User, UserCreate, UserUpdate
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class UserService:
    """ユーザー管理サービス"""

    def __init__(self, user_repository: UserRepository, auth_service: AuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service
        self.logger = logger

    def validate_password_strength(self, password: str) -> bool:
        """
        パスワード強度検証
        
        Requirements:
        - 最小12文字
        - 大文字、小文字、数字、特殊文字を各1文字以上含む
        """
        if len(password) < 12:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        if not any(c in "!@#$%^&*()_+-=" for c in password):
            return False
        return True

    async def create_user(
        self, data: UserCreate, created_by: str
    ) -> User:
        """
        ユーザー作成
        
        Args:
            data: ユーザー作成データ
            created_by: 作成者ユーザーID
        
        Returns:
            User: 作成されたユーザー
        
        Raises:
            ValueError: バリデーションエラー
        """
        # 1. パスワード強度バリデーション
        if not self.validate_password_strength(data.password):
            raise ValueError(
                "Password must be at least 12 characters and contain "
                "uppercase, lowercase, number, and special character"
            )

        # 2. ユーザー名の一意性チェック
        existing_username = await self.user_repository.find_by_username(
            data.username, allow_cross_partition=True
        )
        if existing_username:
            raise ValueError(f"Username '{data.username}' is already taken")

        # 3. メールアドレスの一意性チェック（テナント内）
        existing_email = await self.user_repository.find_by_email(
            data.tenant_id, data.email
        )
        if existing_email:
            raise ValueError(
                f"Email '{data.email}' is already registered in this tenant"
            )

        # 4. パスワードハッシュ化
        password_hash = self.auth_service.hash_password(data.password)

        # 5. Userオブジェクト作成
        user = User(
            tenant_id=data.tenant_id,
            username=data.username,
            email=data.email,
            password_hash=password_hash,
            display_name=data.display_name,
            is_active=True,
            created_by=created_by,
            updated_by=created_by,
        )

        # 6. データベースに保存
        created_user = await self.user_repository.create(user)

        self.logger.info(
            f"User created: {created_user.id} by {created_by}",
            extra={"user_id": created_user.id, "created_by": created_by},
        )

        return created_user

    async def get_user(self, user_id: str, tenant_id: str) -> Optional[User]:
        """ユーザー取得"""
        return await self.user_repository.get(user_id, tenant_id)

    async def update_user(
        self, user_id: str, tenant_id: str, data: UserUpdate, updated_by: str
    ) -> User:
        """
        ユーザー更新
        
        Args:
            user_id: ユーザーID
            tenant_id: テナントID
            data: 更新データ
            updated_by: 更新者ユーザーID
        
        Returns:
            User: 更新されたユーザー
        """
        # メールアドレスの一意性チェック（変更がある場合）
        if data.email:
            existing_email = await self.user_repository.find_by_email(
                tenant_id, data.email
            )
            if existing_email and existing_email.id != user_id:
                raise ValueError(
                    f"Email '{data.email}' is already registered in this tenant"
                )

        # 更新データを辞書に変換
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by
        update_data["updated_at"] = datetime.utcnow()

        # 更新実行
        updated_user = await self.user_repository.update(
            user_id, tenant_id, update_data
        )

        self.logger.info(
            f"User updated: {user_id} by {updated_by}",
            extra={"user_id": user_id, "updated_by": updated_by},
        )

        return updated_user

    async def delete_user(
        self, user_id: str, tenant_id: str, deleted_by: str
    ) -> None:
        """
        ユーザー削除
        
        Args:
            user_id: ユーザーID
            tenant_id: テナントID
            deleted_by: 削除者ユーザーID
        """
        await self.user_repository.delete(user_id, tenant_id)

        self.logger.info(
            f"User deleted: {user_id} by {deleted_by}",
            extra={"user_id": user_id, "deleted_by": deleted_by},
        )

    async def list_users(
        self, tenant_id: str, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """ユーザー一覧取得（テナント内）"""
        return await self.user_repository.list_by_tenant(tenant_id, skip, limit)
