"""UserRepositoryのテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.repositories.user_repository import UserRepository
from app.models.user import User


class TestUserRepository:
    """UserRepositoryのテスト"""

    def setup_method(self):
        """各テストの前に実行"""
        self.mock_container = MagicMock()
        self.repository = UserRepository(self.mock_container)

    class TestCRUD操作:
        """CRUD操作のテスト"""

        @pytest.mark.asyncio
        async def test_create_正常なユーザー作成(self):
            """正常なユーザー作成"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
            )
            
            expected_data = {
                "id": "user_test_001",
                "tenantId": "tenant-test",
                "type": "user",
                "username": "testuser",
                "email": "test@example.com",
                "passwordHash": "hashed",
                "displayName": "Test User",
                "isActive": True,
            }
            
            # AsyncMockを使って非同期関数をモック
            mock_container.create_item = AsyncMock(return_value=expected_data)
            
            # Act
            result = await repository.create(user)
            
            # Assert
            assert result.id == "user_test_001"
            assert result.username == "testuser"
            mock_container.create_item.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_CosmosDBエラー時の例外処理(self):
            """Cosmos DBエラー時の例外処理"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
            )
            
            # CosmosHttpResponseErrorを発生させる
            error = CosmosHttpResponseError(status_code=500, message="Internal error")
            mock_container.create_item = AsyncMock(side_effect=error)
            
            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await repository.create(user)

        @pytest.mark.asyncio
        async def test_get_存在するユーザー取得(self):
            """存在するユーザー取得"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            expected_data = {
                "id": "user_test_001",
                "tenantId": "tenant-test",
                "type": "user",
                "username": "testuser",
                "email": "test@example.com",
                "passwordHash": "hashed",
                "displayName": "Test User",
                "isActive": True,
                "createdAt": "2026-02-01T10:00:00Z",
                "updatedAt": "2026-02-01T10:00:00Z",
            }
            
            mock_container.read_item = AsyncMock(return_value=expected_data)
            
            # Act
            result = await repository.get("user_test_001", "tenant-test")
            
            # Assert
            assert result is not None
            assert result.id == "user_test_001"
            assert result.username == "testuser"
            mock_container.read_item.assert_called_once_with(
                item="user_test_001", partition_key="tenant-test"
            )

        @pytest.mark.asyncio
        async def test_get_存在しないユーザー取得(self):
            """存在しないユーザー取得（404エラー）"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            error = CosmosHttpResponseError(status_code=404, message="Not found")
            mock_container.read_item = AsyncMock(side_effect=error)
            
            # Act
            result = await repository.get("nonexistent", "tenant-test")
            
            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_get_不正なテナントIDでアクセス(self):
            """不正なテナントIDでアクセス"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            error = CosmosHttpResponseError(status_code=404, message="Not found")
            mock_container.read_item = AsyncMock(side_effect=error)
            
            # Act
            result = await repository.get("user_test_001", "wrong-tenant")
            
            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_update_ユーザー情報更新(self):
            """ユーザー情報更新"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            existing_data = {
                "id": "user_test_001",
                "tenantId": "tenant-test",
                "type": "user",
                "username": "testuser",
                "email": "test@example.com",
                "passwordHash": "hashed",
                "displayName": "Test User",
                "isActive": True,
                "createdAt": "2026-02-01T10:00:00Z",
                "updatedAt": "2026-02-01T10:00:00Z",
            }
            
            updated_data = existing_data.copy()
            updated_data["displayName"] = "Updated Name"
            
            mock_container.read_item = AsyncMock(return_value=existing_data)
            mock_container.upsert_item = AsyncMock(return_value=updated_data)
            
            # Act
            result = await repository.update(
                "user_test_001", "tenant-test", {"display_name": "Updated Name"}
            )
            
            # Assert
            assert result.display_name == "Updated Name"
            mock_container.upsert_item.assert_called_once()

        @pytest.mark.asyncio
        async def test_update_存在しないユーザー更新(self):
            """存在しないユーザー更新"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            error = CosmosHttpResponseError(status_code=404, message="Not found")
            mock_container.read_item = AsyncMock(side_effect=error)
            
            # Act & Assert
            with pytest.raises(ValueError, match="User .* not found"):
                await repository.update(
                    "nonexistent", "tenant-test", {"display_name": "New Name"}
                )

        @pytest.mark.asyncio
        async def test_delete_ユーザー削除(self):
            """ユーザー削除"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            mock_container.delete_item = AsyncMock(return_value=None)
            
            # Act
            await repository.delete("user_test_001", "tenant-test")
            
            # Assert
            mock_container.delete_item.assert_called_once_with(
                item="user_test_001", partition_key="tenant-test"
            )

        @pytest.mark.asyncio
        async def test_delete_存在しないユーザー削除(self):
            """存在しないユーザー削除"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            error = CosmosHttpResponseError(status_code=404, message="Not found")
            mock_container.delete_item = AsyncMock(side_effect=error)
            
            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await repository.delete("nonexistent", "tenant-test")

    class Test検索操作:
        """検索操作のテスト"""

        @pytest.mark.asyncio
        async def test_find_by_username_ユーザー名で検索成功(self):
            """ユーザー名で検索成功"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            user_data = {
                "id": "user_test_001",
                "tenantId": "tenant-test",
                "type": "user",
                "username": "testuser",
                "email": "test@example.com",
                "passwordHash": "hashed",
                "displayName": "Test User",
                "isActive": True,
                "createdAt": "2026-02-01T10:00:00Z",
                "updatedAt": "2026-02-01T10:00:00Z",
            }
            
            # 非同期イテレータを模擬
            async def mock_query():
                yield user_data
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act
            result = await repository.find_by_username("testuser")
            
            # Assert
            assert result is not None
            assert result.username == "testuser"
            mock_container.query_items.assert_called_once()

        @pytest.mark.asyncio
        async def test_find_by_username_存在しないユーザー名(self):
            """存在しないユーザー名で検索"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            # 空の非同期イテレータ
            async def mock_query():
                return
                yield  # この行には到達しない
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act
            result = await repository.find_by_username("nonexistent")
            
            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_find_by_username_クロスパーティションクエリ(self):
            """クロスパーティションクエリ"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            async def mock_query():
                return
                yield
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act
            await repository.find_by_username("testuser", allow_cross_partition=True)
            
            # Assert
            call_kwargs = mock_container.query_items.call_args.kwargs
            assert call_kwargs.get("enable_cross_partition_query") is True

        @pytest.mark.asyncio
        async def test_find_by_email_メールアドレスで検索成功(self):
            """メールアドレスで検索成功"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            user_data = {
                "id": "user_test_001",
                "tenantId": "tenant-test",
                "type": "user",
                "username": "testuser",
                "email": "test@example.com",
                "passwordHash": "hashed",
                "displayName": "Test User",
                "isActive": True,
                "createdAt": "2026-02-01T10:00:00Z",
                "updatedAt": "2026-02-01T10:00:00Z",
            }
            
            async def mock_query():
                yield user_data
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act
            result = await repository.find_by_email("tenant-test", "test@example.com")
            
            # Assert
            assert result is not None
            assert result.email == "test@example.com"

        @pytest.mark.asyncio
        async def test_find_by_email_テナント内スコープ確認(self):
            """テナント内スコープ確認"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            async def mock_query():
                return
                yield
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act
            await repository.find_by_email("tenant-test", "test@example.com")
            
            # Assert
            call_kwargs = mock_container.query_items.call_args.kwargs
            assert call_kwargs.get("partition_key") == "tenant-test"

        @pytest.mark.asyncio
        async def test_list_by_tenant_テナント内ユーザー一覧(self):
            """テナント内ユーザー一覧取得"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            users_data = [
                {
                    "id": f"user_test_{i:03d}",
                    "tenantId": "tenant-test",
                    "type": "user",
                    "username": f"user{i}",
                    "email": f"user{i}@example.com",
                    "passwordHash": "hashed",
                    "displayName": f"User {i}",
                    "isActive": True,
                    "createdAt": "2026-02-01T10:00:00Z",
                    "updatedAt": "2026-02-01T10:00:00Z",
                }
                for i in range(3)
            ]
            
            async def mock_query():
                for user_data in users_data:
                    yield user_data
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act
            result = await repository.list_by_tenant("tenant-test")
            
            # Assert
            assert len(result) == 3
            assert all(isinstance(u, User) for u in result)

        @pytest.mark.asyncio
        async def test_list_by_tenant_ページネーション動作(self):
            """ページネーション動作"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            async def mock_query():
                return
                yield
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act
            await repository.list_by_tenant("tenant-test", skip=10, limit=50)
            
            # Assert
            call_args = mock_container.query_items.call_args
            parameters = call_args.kwargs["parameters"]
            
            skip_param = next(p for p in parameters if p["name"] == "@skip")
            limit_param = next(p for p in parameters if p["name"] == "@limit")
            
            assert skip_param["value"] == 10
            assert limit_param["value"] == 50

        @pytest.mark.asyncio
        async def test_list_by_tenant_空のテナント(self):
            """空のテナント"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            async def mock_query():
                return
                yield
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act
            result = await repository.list_by_tenant("empty-tenant")
            
            # Assert
            assert result == []

    class Test境界値:
        """境界値テスト"""

        @pytest.mark.asyncio
        async def test_list_by_tenant_skip境界値(self):
            """skipパラメータの境界値"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            async def mock_query():
                return
                yield
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act & Assert: skip=0
            await repository.list_by_tenant("tenant-test", skip=0, limit=10)
            parameters = mock_container.query_items.call_args.kwargs["parameters"]
            skip_param = next(p for p in parameters if p["name"] == "@skip")
            assert skip_param["value"] == 0
            
            # Act & Assert: skip=1
            await repository.list_by_tenant("tenant-test", skip=1, limit=10)
            parameters = mock_container.query_items.call_args.kwargs["parameters"]
            skip_param = next(p for p in parameters if p["name"] == "@skip")
            assert skip_param["value"] == 1
            
            # Act & Assert: 大きな値
            await repository.list_by_tenant("tenant-test", skip=10000, limit=10)
            parameters = mock_container.query_items.call_args.kwargs["parameters"]
            skip_param = next(p for p in parameters if p["name"] == "@skip")
            assert skip_param["value"] == 10000

        @pytest.mark.asyncio
        async def test_list_by_tenant_limit境界値(self):
            """limitパラメータの境界値"""
            # Arrange
            mock_container = MagicMock()
            repository = UserRepository(mock_container)
            
            async def mock_query():
                return
                yield
            
            mock_container.query_items = MagicMock(return_value=mock_query())
            
            # Act & Assert: limit=1
            await repository.list_by_tenant("tenant-test", skip=0, limit=1)
            parameters = mock_container.query_items.call_args.kwargs["parameters"]
            limit_param = next(p for p in parameters if p["name"] == "@limit")
            assert limit_param["value"] == 1
            
            # Act & Assert: limit=100
            await repository.list_by_tenant("tenant-test", skip=0, limit=100)
            parameters = mock_container.query_items.call_args.kwargs["parameters"]
            limit_param = next(p for p in parameters if p["name"] == "@limit")
            assert limit_param["value"] == 100
            
            # Act & Assert: limit=1000
            await repository.list_by_tenant("tenant-test", skip=0, limit=1000)
            parameters = mock_container.query_items.call_args.kwargs["parameters"]
            limit_param = next(p for p in parameters if p["name"] == "@limit")
            assert limit_param["value"] == 1000
