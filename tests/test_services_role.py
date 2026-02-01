"""
ロール管理サービスのユニットテスト

テスト対象:
- RoleService.get_available_roles
- RoleService.validate_role
- RoleService.get_user_roles
- RoleService.assign_role
- RoleService.remove_role
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.services.role_service import RoleService
from app.models.role_assignment import RoleAssignment, RoleAssignmentCreate, Role
from app.models.user import User
from datetime import datetime


class TestRoleService:
    """RoleServiceのテストクラス"""
    
    @pytest.fixture
    def mock_role_repository(self):
        """RoleRepositoryのモック"""
        repo = MagicMock()
        repo.create = AsyncMock()
        repo.get = AsyncMock()
        repo.delete = AsyncMock()
        repo.get_by_user_id = AsyncMock()
        repo.find_by_user_and_service = AsyncMock()
        repo.create_if_not_exists = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_user_repository(self):
        """UserRepositoryのモック"""
        repo = MagicMock()
        repo.get = AsyncMock()
        return repo
    
    @pytest.fixture
    def role_service(self, mock_role_repository, mock_user_repository):
        """RoleServiceのインスタンス"""
        return RoleService(mock_role_repository, mock_user_repository)
    
    @pytest.fixture
    def sample_user(self):
        """サンプルユーザーデータ"""
        return User(
            id="user_test_001",
            tenant_id="tenant-test",
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            password_hash="hashed_password",
            is_active=True,
        )
    
    @pytest.fixture
    def sample_role_assignment(self):
        """サンプルRoleAssignmentデータ"""
        return RoleAssignment(
            id="role_assignment_001",
            tenant_id="tenant-test",
            user_id="user_test_001",
            service_id="auth-service",
            role_name="全体管理者",
            assigned_by="user_admin",
        )
    
    class Test_get_available_roles:
        """get_available_rolesメソッドのテスト"""
        
        def test_get_available_roles_全ロール取得(self, role_service):
            """TC-SVC-R-GAR-001"""
            # Act
            roles = role_service.get_available_roles()
            
            # Assert
            assert isinstance(roles, list)
            assert len(roles) == 4  # auth-service 2件 + tenant-management 2件
            assert all(isinstance(role, Role) for role in roles)
            assert all(hasattr(role, 'service_id') for role in roles)
            assert all(hasattr(role, 'role_name') for role in roles)
            assert all(hasattr(role, 'description') for role in roles)
        
        def test_get_available_roles_認証サービスのロールが含まれる(self, role_service):
            """TC-SVC-R-GAR-002"""
            # Act
            roles = role_service.get_available_roles()
            
            # Assert
            auth_roles = [r for r in roles if r.service_id == "auth-service"]
            assert len(auth_roles) == 2
            role_names = [r.role_name for r in auth_roles]
            assert "全体管理者" in role_names
            assert "閲覧者" in role_names
        
        def test_get_available_roles_テナント管理サービスのロールが含まれる(self, role_service):
            """TC-SVC-R-GAR-003"""
            # Act
            roles = role_service.get_available_roles()
            
            # Assert
            tenant_roles = [r for r in roles if r.service_id == "tenant-management"]
            assert len(tenant_roles) == 2
            role_names = [r.role_name for r in tenant_roles]
            assert "管理者" in role_names
            assert "閲覧者" in role_names
    
    class Test_validate_role:
        """validate_roleメソッドのテスト"""
        
        def test_validate_role_有効なロール_auth_service_全体管理者(self, role_service):
            """TC-SVC-R-VR-001"""
            # Act
            result = role_service.validate_role("auth-service", "全体管理者")
            
            # Assert
            assert result is True
        
        def test_validate_role_有効なロール_tenant_management_管理者(self, role_service):
            """TC-SVC-R-VR-002"""
            # Act
            result = role_service.validate_role("tenant-management", "管理者")
            
            # Assert
            assert result is True
        
        def test_validate_role_無効なサービスID(self, role_service):
            """TC-SVC-R-VR-E-001"""
            # Act
            result = role_service.validate_role("invalid-service", "管理者")
            
            # Assert
            assert result is False
        
        def test_validate_role_無効なロール名(self, role_service):
            """TC-SVC-R-VR-E-002"""
            # Act
            result = role_service.validate_role("auth-service", "無効なロール")
            
            # Assert
            assert result is False
        
        def test_validate_role_サービスIDとロール名の組み合わせが不正(self, role_service):
            """TC-SVC-R-VR-E-003"""
            # Act
            # auth-serviceには"管理者"というロールは存在しない（tenant-managementのロール）
            result = role_service.validate_role("auth-service", "管理者")
            
            # Assert
            assert result is False
    
    class Test_get_user_roles:
        """get_user_rolesメソッドのテスト"""
        
        @pytest.mark.asyncio
        async def test_get_user_roles_複数件取得(
            self, role_service, mock_user_repository, mock_role_repository, sample_user
        ):
            """TC-SVC-R-GUR-001"""
            # Arrange
            mock_user_repository.get.return_value = sample_user
            role_assignments = [
                RoleAssignment(
                    id="role_assignment_001",
                    tenant_id="tenant-test",
                    user_id="user_test_001",
                    service_id="auth-service",
                    role_name="全体管理者",
                    assigned_by="user_admin",
                ),
                RoleAssignment(
                    id="role_assignment_002",
                    tenant_id="tenant-test",
                    user_id="user_test_001",
                    service_id="tenant-management",
                    role_name="管理者",
                    assigned_by="user_admin",
                ),
            ]
            mock_role_repository.get_by_user_id.return_value = role_assignments
            
            # Act
            result = await role_service.get_user_roles("user_test_001", "tenant-test")
            
            # Assert
            assert len(result) == 2
            assert result[0].service_id == "auth-service"
            assert result[1].service_id == "tenant-management"
        
        @pytest.mark.asyncio
        async def test_get_user_roles_0件取得(
            self, role_service, mock_user_repository, mock_role_repository, sample_user
        ):
            """TC-SVC-R-GUR-002"""
            # Arrange
            mock_user_repository.get.return_value = sample_user
            mock_role_repository.get_by_user_id.return_value = []
            
            # Act
            result = await role_service.get_user_roles("user_test_001", "tenant-test")
            
            # Assert
            assert len(result) == 0
        
        @pytest.mark.asyncio
        async def test_get_user_roles_ユーザー不存在(
            self, role_service, mock_user_repository, mock_role_repository
        ):
            """TC-SVC-R-GUR-E-001"""
            # Arrange
            mock_user_repository.get.return_value = None
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await role_service.get_user_roles("user_test_001", "tenant-test")
            
            assert exc_info.value.status_code == 404
            assert "ROLE_001_USER_NOT_FOUND" in str(exc_info.value.detail)
    
    class Test_assign_role:
        """assign_roleメソッドのテスト"""
        
        @pytest.mark.asyncio
        async def test_assign_role_正常な割り当て(
            self, role_service, mock_user_repository, mock_role_repository, sample_user
        ):
            """TC-SVC-R-AR-001"""
            # Arrange
            mock_user_repository.get.return_value = sample_user
            data = RoleAssignmentCreate(
                tenant_id="tenant-test",
                service_id="auth-service",
                role_name="全体管理者",
            )
            new_assignment = RoleAssignment(
                id="role_assignment_001",
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            mock_role_repository.create_if_not_exists.return_value = (new_assignment, True)
            
            # Act
            result = await role_service.assign_role("user_test_001", data, "user_admin")
            
            # Assert
            assert result.id == "role_assignment_001"
            mock_role_repository.create_if_not_exists.assert_called_once()
        
        @pytest.mark.asyncio
        async def test_assign_role_auth_service_全体管理者(
            self, role_service, mock_user_repository, mock_role_repository, sample_user
        ):
            """TC-SVC-R-AR-002"""
            # Arrange
            mock_user_repository.get.return_value = sample_user
            data = RoleAssignmentCreate(
                tenant_id="tenant-test",
                service_id="auth-service",
                role_name="全体管理者",
            )
            new_assignment = RoleAssignment(
                id="role_assignment_001",
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            mock_role_repository.create_if_not_exists.return_value = (new_assignment, True)
            
            # Act
            result = await role_service.assign_role("user_test_001", data, "user_admin")
            
            # Assert
            assert result.service_id == "auth-service"
            assert result.role_name == "全体管理者"
        
        @pytest.mark.asyncio
        async def test_assign_role_tenant_management_管理者(
            self, role_service, mock_user_repository, mock_role_repository, sample_user
        ):
            """TC-SVC-R-AR-003"""
            # Arrange
            mock_user_repository.get.return_value = sample_user
            data = RoleAssignmentCreate(
                tenant_id="tenant-test",
                service_id="tenant-management",
                role_name="管理者",
            )
            new_assignment = RoleAssignment(
                id="role_assignment_002",
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="tenant-management",
                role_name="管理者",
                assigned_by="user_admin",
            )
            mock_role_repository.create_if_not_exists.return_value = (new_assignment, True)
            
            # Act
            result = await role_service.assign_role("user_test_001", data, "user_admin")
            
            # Assert
            assert result.service_id == "tenant-management"
            assert result.role_name == "管理者"
        
        @pytest.mark.asyncio
        async def test_assign_role_ユーザー不存在(
            self, role_service, mock_user_repository, mock_role_repository
        ):
            """TC-SVC-R-AR-E-001"""
            # Arrange
            mock_user_repository.get.return_value = None
            data = RoleAssignmentCreate(
                tenant_id="tenant-test",
                service_id="auth-service",
                role_name="全体管理者",
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await role_service.assign_role("user_test_001", data, "user_admin")
            
            assert exc_info.value.status_code == 404
            assert "ROLE_001_USER_NOT_FOUND" in str(exc_info.value.detail)
        
        @pytest.mark.asyncio
        async def test_assign_role_無効なロール(
            self, role_service, mock_user_repository, mock_role_repository, sample_user
        ):
            """TC-SVC-R-AR-E-002"""
            # Arrange
            mock_user_repository.get.return_value = sample_user
            data = RoleAssignmentCreate(
                tenant_id="tenant-test",
                service_id="invalid-service",
                role_name="無効なロール",
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await role_service.assign_role("user_test_001", data, "user_admin")
            
            assert exc_info.value.status_code == 400
            assert "ROLE_005_INVALID_ROLE" in str(exc_info.value.detail)
        
        @pytest.mark.asyncio
        async def test_assign_role_重複割り当て(
            self, role_service, mock_user_repository, mock_role_repository, sample_user
        ):
            """TC-SVC-R-AR-E-003"""
            # Arrange
            mock_user_repository.get.return_value = sample_user
            data = RoleAssignmentCreate(
                tenant_id="tenant-test",
                service_id="auth-service",
                role_name="全体管理者",
            )
            existing_assignment = RoleAssignment(
                id="role_assignment_001",
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            mock_role_repository.create_if_not_exists.return_value = (existing_assignment, False)
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await role_service.assign_role("user_test_001", data, "user_admin")
            
            assert exc_info.value.status_code == 409
            assert "ROLE_002_DUPLICATE_ASSIGNMENT" in str(exc_info.value.detail)
    
    class Test_remove_role:
        """remove_roleメソッドのテスト"""
        
        @pytest.mark.asyncio
        async def test_remove_role_正常な削除(
            self, role_service, mock_role_repository, sample_role_assignment
        ):
            """TC-SVC-R-RR-001"""
            # Arrange
            mock_role_repository.get.return_value = sample_role_assignment
            mock_role_repository.delete.return_value = None
            
            # Act
            await role_service.remove_role("user_test_001", "role_assignment_001", "tenant-test")
            
            # Assert
            mock_role_repository.delete.assert_called_once_with("role_assignment_001", "tenant-test")
        
        @pytest.mark.asyncio
        async def test_remove_role_ロール割り当て不存在(
            self, role_service, mock_role_repository
        ):
            """TC-SVC-R-RR-E-001"""
            # Arrange
            mock_role_repository.get.return_value = None
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await role_service.remove_role("user_test_001", "role_assignment_001", "tenant-test")
            
            assert exc_info.value.status_code == 404
            assert "ROLE_003_ASSIGNMENT_NOT_FOUND" in str(exc_info.value.detail)
        
        @pytest.mark.asyncio
        async def test_remove_role_ユーザーID不一致(
            self, role_service, mock_role_repository
        ):
            """TC-SVC-R-RR-E-002"""
            # Arrange
            other_user_assignment = RoleAssignment(
                id="role_assignment_001",
                tenant_id="tenant-test",
                user_id="other_user_id",  # 異なるユーザーID
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by="user_admin",
            )
            mock_role_repository.get.return_value = other_user_assignment
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await role_service.remove_role("user_test_001", "role_assignment_001", "tenant-test")
            
            assert exc_info.value.status_code == 400
            assert "ROLE_003_ASSIGNMENT_NOT_FOUND" in str(exc_info.value.detail)
