"""ユーザーサービスのテスト"""
import pytest
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.models.user import UserCreate, UserUpdate
from unittest.mock import AsyncMock, MagicMock


class TestUserService:
    """ユーザーサービステストクラス"""

    def setup_method(self):
        """各テストの前に実行"""
        self.user_repository = MagicMock()
        self.auth_service = MagicMock(spec=AuthService)
        self.service = UserService(self.user_repository, self.auth_service)

    class Testパスワード強度検証:
        """パスワード強度検証のテスト"""

        def setup_method(self):
            """各テストの前に実行"""
            self.user_repository = MagicMock()
            self.auth_service = MagicMock(spec=AuthService)
            self.service = UserService(self.user_repository, self.auth_service)

        def test_validate_password_strength_有効(self):
            """パスワード強度バリデーション（有効）"""
            password = "TestP@ssw0rd123"
            assert self.service.validate_password_strength(password) is True

        def test_validate_password_strength_短すぎる(self):
            """パスワード強度バリデーション（短すぎる）"""
            password = "Test@123"
            assert self.service.validate_password_strength(password) is False

        def test_validate_password_strength_12文字ちょうど(self):
            """パスワード強度バリデーション（12文字ちょうど）"""
            password = "TestP@ss123w"
            assert self.service.validate_password_strength(password) is True

        def test_validate_password_strength_11文字(self):
            """パスワード強度バリデーション（11文字・境界値）"""
            password = "TestP@ss12w"
            assert self.service.validate_password_strength(password) is False

        def test_validate_password_strength_大文字なし(self):
            """パスワード強度バリデーション（大文字なし）"""
            password = "testp@ssw0rd123"
            assert self.service.validate_password_strength(password) is False

        def test_validate_password_strength_小文字なし(self):
            """パスワード強度バリデーション（小文字なし）"""
            password = "TESTP@SSW0RD123"
            assert self.service.validate_password_strength(password) is False

        def test_validate_password_strength_数字なし(self):
            """パスワード強度バリデーション（数字なし）"""
            password = "TestP@ssword"
            assert self.service.validate_password_strength(password) is False

        def test_validate_password_strength_特殊文字なし(self):
            """パスワード強度バリデーション（特殊文字なし）"""
            password = "TestPassword123"
            assert self.service.validate_password_strength(password) is False

    class Testユーザー作成:
        """ユーザー作成のテスト"""

        @pytest.mark.asyncio
        async def test_create_user_正常な作成(self):
            """正常なユーザー作成"""
            # Arrange
            from app.models.user import User
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            user_data = UserCreate(
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password="ValidP@ssw0rd123",
                display_name="Test User",
            )
            
            # モック設定
            user_repository.find_by_username = AsyncMock(return_value=None)
            user_repository.find_by_email = AsyncMock(return_value=None)
            auth_service.hash_password = MagicMock(return_value="hashed_password")
            
            created_user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed_password",
                display_name="Test User",
                is_active=True,
            )
            user_repository.create = AsyncMock(return_value=created_user)
            
            # Act
            result = await service.create_user(user_data, "admin")
            
            # Assert
            assert result.id == "user_test_001"
            assert result.username == "testuser"
            auth_service.hash_password.assert_called_once_with("ValidP@ssw0rd123")

        @pytest.mark.asyncio
        async def test_create_user_弱いパスワード(self):
            """弱いパスワードでユーザー作成"""
            # Arrange
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            user_data = UserCreate(
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password="weak",  # 弱いパスワード
                display_name="Test User",
            )
            
            # Act & Assert
            with pytest.raises(ValueError, match="Password must be at least"):
                await service.create_user(user_data, "admin")

        @pytest.mark.asyncio
        async def test_create_user_重複ユーザー名(self):
            """重複ユーザー名でユーザー作成"""
            # Arrange
            from app.models.user import User
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            user_data = UserCreate(
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password="ValidP@ssw0rd123",
                display_name="Test User",
            )
            
            # 既存ユーザー
            existing_user = User(
                id="user_existing",
                tenant_id="tenant-other",
                username="testuser",
                email="other@example.com",
                password_hash="hashed",
                display_name="Existing User",
            )
            user_repository.find_by_username = AsyncMock(return_value=existing_user)
            
            # Act & Assert
            with pytest.raises(ValueError, match="Username .* is already taken"):
                await service.create_user(user_data, "admin")

        @pytest.mark.asyncio
        async def test_create_user_重複メールアドレス(self):
            """重複メールアドレスでユーザー作成"""
            # Arrange
            from app.models.user import User
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            user_data = UserCreate(
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password="ValidP@ssw0rd123",
                display_name="Test User",
            )
            
            # ユーザー名は重複なし
            user_repository.find_by_username = AsyncMock(return_value=None)
            
            # メールが重複
            existing_user = User(
                id="user_existing",
                tenant_id="tenant-test",
                username="otheruser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Existing User",
            )
            user_repository.find_by_email = AsyncMock(return_value=existing_user)
            
            # Act & Assert
            with pytest.raises(ValueError, match="Email .* is already registered"):
                await service.create_user(user_data, "admin")

        @pytest.mark.asyncio
        async def test_create_user_監査ログ設定(self):
            """監査ログ（created_by）設定"""
            # Arrange
            from app.models.user import User
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            user_data = UserCreate(
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password="ValidP@ssw0rd123",
                display_name="Test User",
            )
            
            user_repository.find_by_username = AsyncMock(return_value=None)
            user_repository.find_by_email = AsyncMock(return_value=None)
            auth_service.hash_password = MagicMock(return_value="hashed_password")
            
            # createメソッドに渡されたUserオブジェクトを検証
            async def check_created_by(user):
                assert user.created_by == "admin_user"
                assert user.updated_by == "admin_user"
                return user
            
            user_repository.create = AsyncMock(side_effect=check_created_by)
            
            # Act
            await service.create_user(user_data, "admin_user")
            
            # Assert
            user_repository.create.assert_called_once()

    class Testユーザー更新:
        """ユーザー更新のテスト"""

        @pytest.mark.asyncio
        async def test_update_user_正常な更新(self):
            """正常なユーザー更新"""
            # Arrange
            from app.models.user import User
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            update_data = UserUpdate(display_name="Updated Name")
            
            updated_user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Updated Name",
                is_active=True,
            )
            user_repository.update = AsyncMock(return_value=updated_user)
            
            # Act
            result = await service.update_user(
                "user_test_001", "tenant-test", update_data, "admin"
            )
            
            # Assert
            assert result.display_name == "Updated Name"

        @pytest.mark.asyncio
        async def test_update_user_重複メールアドレス(self):
            """重複メールアドレスで更新"""
            # Arrange
            from app.models.user import User
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            update_data = UserUpdate(email="duplicate@example.com")
            
            # 他のユーザーが同じメールを使用
            existing_user = User(
                id="user_other",
                tenant_id="tenant-test",
                username="otheruser",
                email="duplicate@example.com",
                password_hash="hashed",
                display_name="Other User",
            )
            user_repository.find_by_email = AsyncMock(return_value=existing_user)
            
            # Act & Assert
            with pytest.raises(ValueError, match="Email .* is already registered"):
                await service.update_user(
                    "user_test_001", "tenant-test", update_data, "admin"
                )

        @pytest.mark.asyncio
        async def test_update_user_監査ログ設定(self):
            """監査ログ（updated_by）設定"""
            # Arrange
            from app.models.user import User
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            update_data = UserUpdate(display_name="Updated Name")
            
            # updateメソッドに渡されたデータを検証
            async def check_updated_by(user_id, tenant_id, data):
                assert data["updated_by"] == "admin_user"
                return User(
                    id=user_id,
                    tenant_id=tenant_id,
                    username="testuser",
                    email="test@example.com",
                    password_hash="hashed",
                    display_name="Updated Name",
                    is_active=True,
                )
            
            user_repository.update = AsyncMock(side_effect=check_updated_by)
            
            # Act
            await service.update_user(
                "user_test_001", "tenant-test", update_data, "admin_user"
            )
            
            # Assert
            user_repository.update.assert_called_once()

    class Testユーザー取得削除:
        """ユーザー取得・削除のテスト"""

        @pytest.mark.asyncio
        async def test_get_user_正常な取得(self):
            """正常なユーザー取得"""
            # Arrange
            from app.models.user import User
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
                is_active=True,
            )
            user_repository.get = AsyncMock(return_value=user)
            
            # Act
            result = await service.get_user("user_test_001", "tenant-test")
            
            # Assert
            assert result.id == "user_test_001"

        @pytest.mark.asyncio
        async def test_delete_user_正常な削除(self):
            """正常なユーザー削除"""
            # Arrange
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            user_repository.delete = AsyncMock(return_value=None)
            
            # Act
            await service.delete_user("user_test_001", "tenant-test", "admin")
            
            # Assert
            user_repository.delete.assert_called_once_with(
                "user_test_001", "tenant-test"
            )

        @pytest.mark.asyncio
        async def test_list_users_正常な一覧取得(self):
            """正常なユーザー一覧取得"""
            # Arrange
            from app.models.user import User
            user_repository = MagicMock()
            auth_service = MagicMock(spec=AuthService)
            service = UserService(user_repository, auth_service)
            
            users = [
                User(
                    id=f"user_test_{i:03d}",
                    tenant_id="tenant-test",
                    username=f"user{i}",
                    email=f"user{i}@example.com",
                    password_hash="hashed",
                    display_name=f"User {i}",
                    is_active=True,
                )
                for i in range(3)
            ]
            user_repository.list_by_tenant = AsyncMock(return_value=users)
            
            # Act
            result = await service.list_users("tenant-test")
            
            # Assert
            assert len(result) == 3
            assert all(u.tenant_id == "tenant-test" for u in result)
