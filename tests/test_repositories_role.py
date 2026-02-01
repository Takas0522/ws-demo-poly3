"""
ロール割り当てリポジトリのユニットテスト

テスト対象:
- RoleRepository.create
- RoleRepository.get
- RoleRepository.delete
- RoleRepository.get_by_user_id
- RoleRepository.find_by_user_and_service
- RoleRepository.create_if_not_exists
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.repositories.role_repository import RoleRepository
from app.models.role_assignment import RoleAssignment


class TestRoleRepository:
    """RoleRepositoryのテストクラス"""
    
    @pytest.fixture
    def mock_container(self):
        """Cosmos DBコンテナのモック"""
        container = MagicMock()
        container.create_item = AsyncMock()
        container.read_item = AsyncMock()
        container.delete_item = AsyncMock()
        container.query_items = MagicMock()
        return container
    
    @pytest.fixture
    def role_repository(self, mock_container):
        """RoleRepositoryのインスタンス"""
        return RoleRepository(mock_container)
    
    @pytest.fixture
    def sample_role_assignment(self):
        """サンプルRoleAssignmentデータ"""
        return RoleAssignment(
            id="role_assignment_test_001",
            tenant_id="tenant-test",
            user_id="user_test_001",
            service_id="auth-service",
            role_name="全体管理者",
            assigned_by="user_admin",
        )
    
    class Test_create:
        """createメソッドのテスト"""
        
        @pytest.mark.asyncio
        async def test_create_正常な作成(self, role_repository, mock_container, sample_role_assignment):
            """TC-REPO-R-CREATE-001"""
            # Arrange
            mock_container.create_item.return_value = sample_role_assignment.model_dump(by_alias=True)
            
            # Act
            result = await role_repository.create(sample_role_assignment)
            
            # Assert
            assert result.id == sample_role_assignment.id
            assert result.tenant_id == sample_role_assignment.tenant_id
            assert result.user_id == sample_role_assignment.user_id
            mock_container.create_item.assert_called_once()
        
        @pytest.mark.asyncio
        async def test_create_Cosmos_DBエラー(self, role_repository, mock_container, sample_role_assignment):
            """TC-REPO-R-CREATE-E-001"""
            # Arrange
            mock_container.create_item.side_effect = CosmosHttpResponseError(status_code=500, message="Server error")
            
            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await role_repository.create(sample_role_assignment)
    
    class Test_get:
        """getメソッドのテスト"""
        
        @pytest.mark.asyncio
        async def test_get_正常な取得(self, role_repository, mock_container):
            """TC-REPO-R-GET-001"""
            # Arrange
            role_assignment_data = {
                "id": "role_assignment_test_001",
                "tenantId": "tenant-test",
                "userId": "user_test_001",
                "serviceId": "auth-service",
                "roleName": "全体管理者",
                "assignedBy": "user_admin",
                "assignedAt": datetime.utcnow(),
                "createdAt": datetime.utcnow(),
                "type": "role_assignment",
            }
            mock_container.read_item.return_value = role_assignment_data
            
            # Act
            result = await role_repository.get("role_assignment_test_001", "tenant-test")
            
            # Assert
            assert result is not None
            assert result.id == "role_assignment_test_001"
            assert result.tenant_id == "tenant-test"
            mock_container.read_item.assert_called_once_with(
                item="role_assignment_test_001",
                partition_key="tenant-test"
            )
        
        @pytest.mark.asyncio
        async def test_get_存在しないロール割り当て(self, role_repository, mock_container):
            """TC-REPO-R-GET-E-001"""
            # Arrange
            mock_container.read_item.side_effect = CosmosHttpResponseError(status_code=404, message="Not found")
            
            # Act
            result = await role_repository.get("role_assignment_not_found", "tenant-test")
            
            # Assert
            assert result is None
        
        @pytest.mark.asyncio
        async def test_get_Cosmos_DBエラー_404以外(self, role_repository, mock_container):
            """TC-REPO-R-GET-E-002"""
            # Arrange
            mock_container.read_item.side_effect = CosmosHttpResponseError(status_code=500, message="Server error")
            
            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await role_repository.get("role_assignment_test_001", "tenant-test")
    
    class Test_delete:
        """deleteメソッドのテスト"""
        
        @pytest.mark.asyncio
        async def test_delete_正常な削除(self, role_repository, mock_container):
            """TC-REPO-R-DELETE-001"""
            # Arrange
            mock_container.delete_item.return_value = None
            
            # Act
            await role_repository.delete("role_assignment_test_001", "tenant-test")
            
            # Assert
            mock_container.delete_item.assert_called_once_with(
                item="role_assignment_test_001",
                partition_key="tenant-test"
            )
        
        @pytest.mark.asyncio
        async def test_delete_Cosmos_DBエラー(self, role_repository, mock_container):
            """TC-REPO-R-DELETE-E-001"""
            # Arrange
            mock_container.delete_item.side_effect = CosmosHttpResponseError(status_code=500, message="Server error")
            
            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await role_repository.delete("role_assignment_test_001", "tenant-test")
    
    class Test_get_by_user_id:
        """get_by_user_idメソッドのテスト"""
        
        @pytest.mark.asyncio
        async def test_get_by_user_id_複数件取得(self, role_repository, mock_container):
            """TC-REPO-R-GETBYUID-001"""
            # Arrange
            role_assignments_data = [
                {
                    "id": "role_assignment_001",
                    "tenantId": "tenant-test",
                    "userId": "user_test_001",
                    "serviceId": "auth-service",
                    "roleName": "全体管理者",
                    "assignedBy": "user_admin",
                    "assignedAt": datetime.utcnow(),
                    "createdAt": datetime.utcnow(),
                    "type": "role_assignment",
                },
                {
                    "id": "role_assignment_002",
                    "tenantId": "tenant-test",
                    "userId": "user_test_001",
                    "serviceId": "tenant-management",
                    "roleName": "管理者",
                    "assignedBy": "user_admin",
                    "assignedAt": datetime.utcnow(),
                    "createdAt": datetime.utcnow(),
                    "type": "role_assignment",
                },
            ]
            
            async def mock_query_items(*args, **kwargs):
                for item in role_assignments_data:
                    yield item
            
            mock_container.query_items.return_value = mock_query_items()
            
            # Act
            result = await role_repository.get_by_user_id("user_test_001", "tenant-test")
            
            # Assert
            assert len(result) == 2
            assert result[0].id == "role_assignment_001"
            assert result[1].id == "role_assignment_002"
            mock_container.query_items.assert_called_once()
        
        @pytest.mark.asyncio
        async def test_get_by_user_id_0件取得(self, role_repository, mock_container):
            """TC-REPO-R-GETBYUID-002"""
            # Arrange
            async def mock_query_items(*args, **kwargs):
                return
                yield  # This makes it a generator but yields nothing
            
            mock_container.query_items.return_value = mock_query_items()
            
            # Act
            result = await role_repository.get_by_user_id("user_test_001", "tenant-test")
            
            # Assert
            assert len(result) == 0
        
        @pytest.mark.asyncio
        async def test_get_by_user_id_クエリパラメータの検証(self, role_repository, mock_container):
            """TC-REPO-R-GETBYUID-003"""
            # Arrange
            async def mock_query_items(*args, **kwargs):
                return
                yield
            
            mock_container.query_items.return_value = mock_query_items()
            
            # Act
            await role_repository.get_by_user_id("user_test_001", "tenant-test")
            
            # Assert
            call_args = mock_container.query_items.call_args
            assert "query" in call_args.kwargs
            assert "parameters" in call_args.kwargs
            assert "partition_key" in call_args.kwargs
            
            parameters = call_args.kwargs["parameters"]
            assert any(p["name"] == "@tenant_id" and p["value"] == "tenant-test" for p in parameters)
            assert any(p["name"] == "@user_id" and p["value"] == "user_test_001" for p in parameters)
            assert call_args.kwargs["partition_key"] == "tenant-test"
        
        @pytest.mark.asyncio
        async def test_get_by_user_id_Cosmos_DBエラー(self, role_repository, mock_container):
            """TC-REPO-R-GETBYUID-E-001"""
            # Arrange
            mock_container.query_items.side_effect = CosmosHttpResponseError(status_code=500, message="Server error")
            
            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await role_repository.get_by_user_id("user_test_001", "tenant-test")
    
    class Test_find_by_user_and_service:
        """find_by_user_and_serviceメソッドのテスト"""
        
        @pytest.mark.asyncio
        async def test_find_by_user_and_service_存在する場合(self, role_repository, mock_container):
            """TC-REPO-R-FIND-001"""
            # Arrange
            role_assignment_data = {
                "id": "role_assignment_001",
                "tenantId": "tenant-test",
                "userId": "user_test_001",
                "serviceId": "auth-service",
                "roleName": "全体管理者",
                "assignedBy": "user_admin",
                "assignedAt": datetime.utcnow(),
                "createdAt": datetime.utcnow(),
                "type": "role_assignment",
            }
            
            async def mock_query_items(*args, **kwargs):
                yield role_assignment_data
            
            mock_container.query_items.return_value = mock_query_items()
            
            # Act
            result = await role_repository.find_by_user_and_service(
                "user_test_001", "tenant-test", "auth-service", "全体管理者"
            )
            
            # Assert
            assert result is not None
            assert result.id == "role_assignment_001"
        
        @pytest.mark.asyncio
        async def test_find_by_user_and_service_存在しない場合(self, role_repository, mock_container):
            """TC-REPO-R-FIND-002"""
            # Arrange
            async def mock_query_items(*args, **kwargs):
                return
                yield
            
            mock_container.query_items.return_value = mock_query_items()
            
            # Act
            result = await role_repository.find_by_user_and_service(
                "user_test_001", "tenant-test", "auth-service", "全体管理者"
            )
            
            # Assert
            assert result is None
        
        @pytest.mark.asyncio
        async def test_find_by_user_and_service_クエリパラメータの検証(self, role_repository, mock_container):
            """TC-REPO-R-FIND-003"""
            # Arrange
            async def mock_query_items(*args, **kwargs):
                return
                yield
            
            mock_container.query_items.return_value = mock_query_items()
            
            # Act
            await role_repository.find_by_user_and_service(
                "user_test_001", "tenant-test", "auth-service", "全体管理者"
            )
            
            # Assert
            call_args = mock_container.query_items.call_args
            parameters = call_args.kwargs["parameters"]
            assert any(p["name"] == "@tenant_id" and p["value"] == "tenant-test" for p in parameters)
            assert any(p["name"] == "@user_id" and p["value"] == "user_test_001" for p in parameters)
            assert any(p["name"] == "@service_id" and p["value"] == "auth-service" for p in parameters)
            assert any(p["name"] == "@role_name" and p["value"] == "全体管理者" for p in parameters)
        
        @pytest.mark.asyncio
        async def test_find_by_user_and_service_Cosmos_DBエラー(self, role_repository, mock_container):
            """TC-REPO-R-FIND-E-001"""
            # Arrange
            mock_container.query_items.side_effect = CosmosHttpResponseError(status_code=500, message="Server error")
            
            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await role_repository.find_by_user_and_service(
                    "user_test_001", "tenant-test", "auth-service", "全体管理者"
                )
    
    class Test_create_if_not_exists:
        """create_if_not_existsメソッドのテスト"""
        
        @pytest.mark.asyncio
        async def test_create_if_not_exists_新規作成(self, role_repository, mock_container):
            """TC-REPO-R-CINE-001"""
            # Arrange
            async def mock_query_items(*args, **kwargs):
                return
                yield
            
            mock_container.query_items.return_value = mock_query_items()
            
            deterministic_id = "ra_user_test_001_auth-service_全体管理者"
            created_data = {
                "id": deterministic_id,
                "tenantId": "tenant-test",
                "userId": "user_test_001",
                "serviceId": "auth-service",
                "roleName": "全体管理者",
                "assignedBy": "user_admin",
                "assignedAt": datetime.utcnow(),
                "createdAt": datetime.utcnow(),
                "type": "role_assignment",
            }
            mock_container.create_item.return_value = created_data
            
            # Act
            result, created = await role_repository.create_if_not_exists(
                "user_test_001", "tenant-test", "auth-service", "全体管理者", "user_admin"
            )
            
            # Assert
            assert created is True
            assert result.id == deterministic_id
        
        @pytest.mark.asyncio
        async def test_create_if_not_exists_既存返却(self, role_repository, mock_container):
            """TC-REPO-R-CINE-002"""
            # Arrange
            existing_data = {
                "id": "role_assignment_001",
                "tenantId": "tenant-test",
                "userId": "user_test_001",
                "serviceId": "auth-service",
                "roleName": "全体管理者",
                "assignedBy": "user_admin",
                "assignedAt": datetime.utcnow(),
                "createdAt": datetime.utcnow(),
                "type": "role_assignment",
            }
            
            async def mock_query_items(*args, **kwargs):
                yield existing_data
            
            mock_container.query_items.return_value = mock_query_items()
            
            # Act
            result, created = await role_repository.create_if_not_exists(
                "user_test_001", "tenant-test", "auth-service", "全体管理者", "user_admin"
            )
            
            # Assert
            assert created is False
            assert result.id == "role_assignment_001"
            mock_container.create_item.assert_not_called()
        
        @pytest.mark.asyncio
        async def test_create_if_not_exists_競合状態_409エラー(self, role_repository, mock_container):
            """TC-REPO-R-CINE-003"""
            # Arrange
            async def mock_query_items(*args, **kwargs):
                return
                yield
            
            mock_container.query_items.return_value = mock_query_items()
            mock_container.create_item.side_effect = CosmosHttpResponseError(status_code=409, message="Conflict")
            
            deterministic_id = "ra_user_test_001_auth-service_全体管理者"
            existing_data = {
                "id": deterministic_id,
                "tenantId": "tenant-test",
                "userId": "user_test_001",
                "serviceId": "auth-service",
                "roleName": "全体管理者",
                "assignedBy": "user_admin",
                "assignedAt": datetime.utcnow(),
                "createdAt": datetime.utcnow(),
                "type": "role_assignment",
            }
            mock_container.read_item.return_value = existing_data
            
            # Act
            result, created = await role_repository.create_if_not_exists(
                "user_test_001", "tenant-test", "auth-service", "全体管理者", "user_admin"
            )
            
            # Assert
            assert created is False
            assert result.id == deterministic_id
        
        @pytest.mark.asyncio
        async def test_create_if_not_exists_決定的IDの生成(self, role_repository, mock_container):
            """TC-REPO-R-CINE-004"""
            # Arrange
            async def mock_query_items(*args, **kwargs):
                return
                yield
            
            mock_container.query_items.return_value = mock_query_items()
            
            deterministic_id = "ra_user_test_001_auth-service_全体管理者"
            created_data = {
                "id": deterministic_id,
                "tenantId": "tenant-test",
                "userId": "user_test_001",
                "serviceId": "auth-service",
                "roleName": "全体管理者",
                "assignedBy": "user_admin",
                "assignedAt": datetime.utcnow(),
                "createdAt": datetime.utcnow(),
                "type": "role_assignment",
            }
            mock_container.create_item.return_value = created_data
            
            # Act
            result, created = await role_repository.create_if_not_exists(
                "user_test_001", "tenant-test", "auth-service", "全体管理者", "user_admin"
            )
            
            # Assert
            assert result.id == deterministic_id
            assert result.id == "ra_user_test_001_auth-service_全体管理者"
        
        @pytest.mark.asyncio
        async def test_create_if_not_exists_Cosmos_DBエラー_409以外(self, role_repository, mock_container):
            """TC-REPO-R-CINE-E-001"""
            # Arrange
            async def mock_query_items(*args, **kwargs):
                return
                yield
            
            mock_container.query_items.return_value = mock_query_items()
            mock_container.create_item.side_effect = CosmosHttpResponseError(status_code=500, message="Server error")
            
            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await role_repository.create_if_not_exists(
                    "user_test_001", "tenant-test", "auth-service", "全体管理者", "user_admin"
                )
