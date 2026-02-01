"""
ロール管理APIのユニットテスト

テスト対象:
- GET /api/v1/roles
- GET /api/v1/users/{user_id}/roles
- POST /api/v1/users/{user_id}/roles
- DELETE /api/v1/users/{user_id}/roles/{role_assignment_id}
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from fastapi import HTTPException
from datetime import datetime

from app.main import app
from app.api.roles import (
    router,
    get_role_service,
    get_current_user_from_request,
)
from app.models.role_assignment import RoleAssignment, RoleAssignmentCreate, Role


class TestRolesAPI:
    """ロール管理APIのテストクラス"""
    
    @pytest.fixture
    def mock_request(self):
        """Requestオブジェクトのモック"""
        request = Mock()
        request.headers = {
            "X-User-Id": "user_test_001",
            "X-Tenant-Id": "tenant-test",
        }
        return request
    
    @pytest.fixture
    def mock_role_service(self):
        """RoleServiceのモック"""
        service = AsyncMock()
        service.get_available_roles = Mock()
        service.get_user_roles = AsyncMock()
        service.assign_role = AsyncMock()
        service.remove_role = AsyncMock()
        return service
    
    @pytest.fixture
    def current_user(self):
        """現在のユーザー情報"""
        return {
            "user_id": "user_test_001",
            "tenant_id": "tenant-test",
        }
    
    @pytest.fixture
    def sample_roles(self):
        """サンプルロールデータ"""
        return [
            Role(
                service_id="auth-service",
                role_name="全体管理者",
                description="システム全体の管理権限"
            ),
            Role(
                service_id="auth-service",
                role_name="閲覧者",
                description="システム全体の閲覧権限"
            ),
            Role(
                service_id="tenant-management",
                role_name="管理者",
                description="テナント管理の管理権限"
            ),
            Role(
                service_id="tenant-management",
                role_name="閲覧者",
                description="テナント管理の閲覧権限"
            ),
        ]
    
    @pytest.fixture
    def sample_role_assignments(self):
        """サンプルロール割り当てデータ"""
        return [
            RoleAssignment(
                id="role_assignment_001",
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by="user_admin",
                assigned_at=datetime(2024, 1, 1, 0, 0, 0),
                created_at=datetime(2024, 1, 1, 0, 0, 0),
            ),
            RoleAssignment(
                id="role_assignment_002",
                tenant_id="tenant-test",
                user_id="user_test_001",
                service_id="tenant-management",
                role_name="管理者",
                assigned_by="user_admin",
                assigned_at=datetime(2024, 1, 1, 0, 0, 0),
                created_at=datetime(2024, 1, 1, 0, 0, 0),
            ),
        ]
    
    class Test_GET_roles:
        """GET /api/v1/roles のテスト"""
        
        @pytest.mark.asyncio
        async def test_get_available_roles_正常取得(self, async_client, mock_role_service, sample_roles):
            """TC-API-R-GAR-001"""
            mock_role_service.get_available_roles.return_value = sample_roles
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            
            try:
                response = await async_client.get("/api/v1/roles")
                
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert isinstance(data["data"], list)
                assert len(data["data"]) == 4
                
                for role in data["data"]:
                    assert "serviceId" in role
                    assert "roleName" in role
                    assert "description" in role
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_get_available_roles_認証サービスのロールが含まれる(
            self, async_client, mock_role_service, sample_roles
        ):
            """TC-API-R-GAR-002"""
            mock_role_service.get_available_roles.return_value = sample_roles
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            
            try:
                response = await async_client.get("/api/v1/roles")
                
                assert response.status_code == 200
                data = response.json()
                auth_roles = [r for r in data["data"] if r["serviceId"] == "auth-service"]
                assert len(auth_roles) == 2
                role_names = [r["roleName"] for r in auth_roles]
                assert "全体管理者" in role_names
                assert "閲覧者" in role_names
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_get_available_roles_テナント管理サービスのロールが含まれる(
            self, async_client, mock_role_service, sample_roles
        ):
            """TC-API-R-GAR-003"""
            mock_role_service.get_available_roles.return_value = sample_roles
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            
            try:
                response = await async_client.get("/api/v1/roles")
                
                assert response.status_code == 200
                data = response.json()
                tenant_roles = [r for r in data["data"] if r["serviceId"] == "tenant-management"]
                assert len(tenant_roles) == 2
                role_names = [r["roleName"] for r in tenant_roles]
                assert "管理者" in role_names
                assert "閲覧者" in role_names
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_get_available_roles_フィールド名のcamelCase変換(
            self, async_client, mock_role_service, sample_roles
        ):
            """TC-API-R-GAR-004"""
            mock_role_service.get_available_roles.return_value = sample_roles
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            
            try:
                response = await async_client.get("/api/v1/roles")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data["data"]) > 0
                first_role = data["data"][0]
                assert "serviceId" in first_role
                assert "roleName" in first_role
                assert "description" in first_role
                assert "service_id" not in first_role
                assert "role_name" not in first_role
            finally:
                app.dependency_overrides.clear()
    
    class Test_GET_users_user_id_roles:
        """GET /api/v1/users/{user_id}/roles のテスト"""
        
        @pytest.mark.asyncio
        async def test_get_user_roles_正常取得_複数件(
            self, async_client, mock_role_service, current_user, sample_role_assignments
        ):
            """TC-API-R-GUR-001"""
            mock_role_service.get_user_roles.return_value = sample_role_assignments
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.get(
                    f"/api/v1/users/{current_user['user_id']}/roles?tenant_id={current_user['tenant_id']}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert isinstance(data["data"], list)
                assert len(data["data"]) == 2
                mock_role_service.get_user_roles.assert_called_once_with(
                    current_user["user_id"], current_user["tenant_id"]
                )
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_get_user_roles_正常取得_0件(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-GUR-002"""
            mock_role_service.get_user_roles.return_value = []
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.get(
                    f"/api/v1/users/{current_user['user_id']}/roles?tenant_id={current_user['tenant_id']}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert data["data"] == []
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_get_user_roles_テナント分離チェック_同一テナント(
            self, async_client, mock_role_service, current_user, sample_role_assignments
        ):
            """TC-API-R-GUR-003"""
            mock_role_service.get_user_roles.return_value = sample_role_assignments
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.get(
                    f"/api/v1/users/{current_user['user_id']}/roles?tenant_id={current_user['tenant_id']}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "data" in data
                assert len(data["data"]) == 2
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_get_user_roles_テナント分離違反_異なるテナント(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-GUR-E-001"""
            different_tenant_id = "tenant-other"
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.get(
                    f"/api/v1/users/user_other/roles?tenant_id={different_tenant_id}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 403
                data = response.json()
                assert "detail" in data
                assert data["detail"]["error"] == "ROLE_006_TENANT_ISOLATION_VIOLATION"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_get_user_roles_ユーザー不存在(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-GUR-E-002"""
            mock_role_service.get_user_roles.side_effect = HTTPException(
                status_code=404,
                detail={
                    "error": "ROLE_001_USER_NOT_FOUND",
                    "message": "User not found",
                }
            )
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.get(
                    f"/api/v1/users/user_nonexistent/roles?tenant_id={current_user['tenant_id']}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 404
                data = response.json()
                assert "detail" in data
                assert data["detail"]["error"] == "ROLE_001_USER_NOT_FOUND"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_get_user_roles_フィールド名のcamelCase変換(
            self, async_client, mock_role_service, current_user, sample_role_assignments
        ):
            """TC-API-R-GUR-004"""
            mock_role_service.get_user_roles.return_value = sample_role_assignments
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.get(
                    f"/api/v1/users/{current_user['user_id']}/roles?tenant_id={current_user['tenant_id']}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert len(data["data"]) > 0
                first_assignment = data["data"][0]
                assert "userId" in first_assignment
                assert "serviceId" in first_assignment
                assert "roleName" in first_assignment
                assert "assignedBy" in first_assignment
                assert "assignedAt" in first_assignment
                assert "user_id" not in first_assignment
                assert "service_id" not in first_assignment
                assert "role_name" not in first_assignment
                assert "assigned_by" not in first_assignment
                assert "assigned_at" not in first_assignment
            finally:
                app.dependency_overrides.clear()
    
    class Test_POST_users_user_id_roles:
        """POST /api/v1/users/{user_id}/roles のテスト"""
        
        @pytest.mark.asyncio
        async def test_assign_role_正常な割り当て(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-001"""
            new_assignment = RoleAssignment(
                id="role_assignment_new",
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"],
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by=current_user["user_id"],
                assigned_at=datetime(2024, 1, 1, 0, 0, 0),
                created_at=datetime(2024, 1, 1, 0, 0, 0),
            )
            mock_role_service.assign_role.return_value = new_assignment
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.post(
                    f"/api/v1/users/{current_user['user_id']}/roles",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    },
                    json={
                        "tenantId": current_user["tenant_id"],
                        "serviceId": "auth-service",
                        "roleName": "全体管理者",
                    }
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["userId"] == current_user["user_id"]
                assert data["serviceId"] == "auth-service"
                assert data["roleName"] == "全体管理者"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_assign_role_auth_service_全体管理者(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-002"""
            new_assignment = RoleAssignment(
                id="role_assignment_new",
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"],
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by=current_user["user_id"],
                assigned_at=datetime(2024, 1, 1, 0, 0, 0),
                created_at=datetime(2024, 1, 1, 0, 0, 0),
            )
            mock_role_service.assign_role.return_value = new_assignment
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.post(
                    f"/api/v1/users/{current_user['user_id']}/roles",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    },
                    json={
                        "tenantId": current_user["tenant_id"],
                        "serviceId": "auth-service",
                        "roleName": "全体管理者",
                    }
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["serviceId"] == "auth-service"
                assert data["roleName"] == "全体管理者"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_assign_role_tenant_management_管理者(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-003"""
            new_assignment = RoleAssignment(
                id="role_assignment_new",
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"],
                service_id="tenant-management",
                role_name="管理者",
                assigned_by=current_user["user_id"],
                assigned_at=datetime(2024, 1, 1, 0, 0, 0),
                created_at=datetime(2024, 1, 1, 0, 0, 0),
            )
            mock_role_service.assign_role.return_value = new_assignment
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.post(
                    f"/api/v1/users/{current_user['user_id']}/roles",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    },
                    json={
                        "tenantId": current_user["tenant_id"],
                        "serviceId": "tenant-management",
                        "roleName": "管理者",
                    }
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["serviceId"] == "tenant-management"
                assert data["roleName"] == "管理者"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_assign_role_テナント分離チェック_同一テナント(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-004"""
            new_assignment = RoleAssignment(
                id="role_assignment_new",
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"],
                service_id="auth-service",
                role_name="閲覧者",
                assigned_by=current_user["user_id"],
                assigned_at=datetime(2024, 1, 1, 0, 0, 0),
                created_at=datetime(2024, 1, 1, 0, 0, 0),
            )
            mock_role_service.assign_role.return_value = new_assignment
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.post(
                    f"/api/v1/users/{current_user['user_id']}/roles",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    },
                    json={
                        "tenantId": current_user["tenant_id"],
                        "serviceId": "auth-service",
                        "roleName": "閲覧者",
                    }
                )
                
                assert response.status_code == 201
                mock_role_service.assign_role.assert_called_once()
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_assign_role_テナント分離違反_異なるテナント(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-E-001"""
            different_tenant_id = "tenant-other"
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.post(
                    "/api/v1/users/user_other/roles",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    },
                    json={
                        "tenantId": different_tenant_id,
                        "serviceId": "auth-service",
                        "roleName": "全体管理者",
                    }
                )
                
                assert response.status_code == 403
                data = response.json()
                assert "detail" in data
                assert data["detail"]["error"] == "ROLE_006_TENANT_ISOLATION_VIOLATION"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_assign_role_ユーザー不存在(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-E-002"""
            mock_role_service.assign_role.side_effect = HTTPException(
                status_code=404,
                detail={
                    "error": "ROLE_001_USER_NOT_FOUND",
                    "message": "User not found",
                }
            )
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.post(
                    "/api/v1/users/user_nonexistent/roles",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    },
                    json={
                        "tenantId": current_user["tenant_id"],
                        "serviceId": "auth-service",
                        "roleName": "全体管理者",
                    }
                )
                
                assert response.status_code == 404
                data = response.json()
                assert "detail" in data
                assert data["detail"]["error"] == "ROLE_001_USER_NOT_FOUND"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_assign_role_重複割り当て(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-E-003"""
            mock_role_service.assign_role.side_effect = HTTPException(
                status_code=409,
                detail={
                    "error": "ROLE_002_DUPLICATE_ASSIGNMENT",
                    "message": "Role already assigned to user",
                }
            )
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.post(
                    f"/api/v1/users/{current_user['user_id']}/roles",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    },
                    json={
                        "tenantId": current_user["tenant_id"],
                        "serviceId": "auth-service",
                        "roleName": "全体管理者",
                    }
                )
                
                assert response.status_code == 409
                data = response.json()
                assert "detail" in data
                assert data["detail"]["error"] == "ROLE_002_DUPLICATE_ASSIGNMENT"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_assign_role_無効なロール(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-E-004"""
            mock_role_service.assign_role.side_effect = HTTPException(
                status_code=400,
                detail={
                    "error": "ROLE_005_INVALID_ROLE",
                    "message": "Invalid role",
                }
            )
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.post(
                    f"/api/v1/users/{current_user['user_id']}/roles",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    },
                    json={
                        "tenantId": current_user["tenant_id"],
                        "serviceId": "invalid-service",
                        "roleName": "invalid-role",
                    }
                )
                
                assert response.status_code == 400
                data = response.json()
                assert "detail" in data
                assert data["detail"]["error"] == "ROLE_005_INVALID_ROLE"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_assign_role_監査ログ記録(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-005"""
            new_assignment = RoleAssignment(
                id="role_assignment_new",
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"],
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by=current_user["user_id"],
                assigned_at=datetime(2024, 1, 1, 0, 0, 0),
                created_at=datetime(2024, 1, 1, 0, 0, 0),
            )
            mock_role_service.assign_role.return_value = new_assignment
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                with patch("app.api.roles.logger") as mock_logger:
                    response = await async_client.post(
                        f"/api/v1/users/{current_user['user_id']}/roles",
                        headers={
                            "X-User-Id": current_user["user_id"],
                            "X-Tenant-Id": current_user["tenant_id"],
                        },
                        json={
                            "tenantId": current_user["tenant_id"],
                            "serviceId": "auth-service",
                            "roleName": "全体管理者",
                        }
                    )
                
                assert response.status_code == 201
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert call_args[0][0] == "Role assigned"
                extra = call_args[1]["extra"]
                assert extra["action"] == "role.assign"
                assert extra["user_id"] == current_user["user_id"]
                assert extra["tenant_id"] == current_user["tenant_id"]
                assert extra["service_id"] == "auth-service"
                assert extra["role_name"] == "全体管理者"
                assert extra["assigned_by"] == current_user["user_id"]
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_assign_role_フィールド名のcamelCase変換(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-AR-006"""
            new_assignment = RoleAssignment(
                id="role_assignment_new",
                tenant_id=current_user["tenant_id"],
                user_id=current_user["user_id"],
                service_id="auth-service",
                role_name="全体管理者",
                assigned_by=current_user["user_id"],
                assigned_at=datetime(2024, 1, 1, 0, 0, 0),
                created_at=datetime(2024, 1, 1, 0, 0, 0),
            )
            mock_role_service.assign_role.return_value = new_assignment
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.post(
                    f"/api/v1/users/{current_user['user_id']}/roles",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    },
                    json={
                        "tenantId": current_user["tenant_id"],
                        "serviceId": "auth-service",
                        "roleName": "全体管理者",
                    }
                )
                
                assert response.status_code == 201
                data = response.json()
                assert "userId" in data
                assert "serviceId" in data
                assert "roleName" in data
                assert "assignedBy" in data
                assert "assignedAt" in data
                assert "user_id" not in data
                assert "service_id" not in data
                assert "role_name" not in data
                assert "assigned_by" not in data
                assert "assigned_at" not in data
            finally:
                app.dependency_overrides.clear()
    
    class Test_DELETE_users_user_id_roles_role_assignment_id:
        """DELETE /api/v1/users/{user_id}/roles/{role_assignment_id} のテスト"""
        
        @pytest.mark.asyncio
        async def test_remove_role_正常な削除(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-RR-001"""
            mock_role_service.remove_role.return_value = None
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.delete(
                    f"/api/v1/users/{current_user['user_id']}/roles/role_assignment_001?tenant_id={current_user['tenant_id']}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 204
                assert response.text == ""
                mock_role_service.remove_role.assert_called_once_with(
                    current_user["user_id"], "role_assignment_001", current_user["tenant_id"]
                )
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_remove_role_テナント分離チェック_同一テナント(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-RR-002"""
            mock_role_service.remove_role.return_value = None
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.delete(
                    f"/api/v1/users/{current_user['user_id']}/roles/role_assignment_001?tenant_id={current_user['tenant_id']}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 204
                mock_role_service.remove_role.assert_called_once()
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_remove_role_テナント分離違反_異なるテナント(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-RR-E-001"""
            different_tenant_id = "tenant-other"
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.delete(
                    f"/api/v1/users/user_other/roles/role_assignment_001?tenant_id={different_tenant_id}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 403
                data = response.json()
                assert "detail" in data
                assert data["detail"]["error"] == "ROLE_006_TENANT_ISOLATION_VIOLATION"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_remove_role_ロール割り当て不存在(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-RR-E-002"""
            mock_role_service.remove_role.side_effect = HTTPException(
                status_code=404,
                detail={
                    "error": "ROLE_003_ASSIGNMENT_NOT_FOUND",
                    "message": "Role assignment not found",
                }
            )
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                response = await async_client.delete(
                    f"/api/v1/users/{current_user['user_id']}/roles/role_assignment_nonexistent?tenant_id={current_user['tenant_id']}",
                    headers={
                        "X-User-Id": current_user["user_id"],
                        "X-Tenant-Id": current_user["tenant_id"],
                    }
                )
                
                assert response.status_code == 404
                data = response.json()
                assert "detail" in data
                assert data["detail"]["error"] == "ROLE_003_ASSIGNMENT_NOT_FOUND"
            finally:
                app.dependency_overrides.clear()
        
        @pytest.mark.asyncio
        async def test_remove_role_監査ログ記録(
            self, async_client, mock_role_service, current_user
        ):
            """TC-API-R-RR-003"""
            mock_role_service.remove_role.return_value = None
            app.dependency_overrides[get_role_service] = lambda: mock_role_service
            app.dependency_overrides[get_current_user_from_request] = lambda: current_user
            
            try:
                with patch("app.api.roles.logger") as mock_logger:
                    response = await async_client.delete(
                        f"/api/v1/users/{current_user['user_id']}/roles/role_assignment_001?tenant_id={current_user['tenant_id']}",
                        headers={
                            "X-User-Id": current_user["user_id"],
                            "X-Tenant-Id": current_user["tenant_id"],
                        }
                    )
                
                assert response.status_code == 204
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert call_args[0][0] == "Role removed"
                extra = call_args[1]["extra"]
                assert extra["action"] == "role.remove"
                assert extra["user_id"] == current_user["user_id"]
                assert extra["tenant_id"] == current_user["tenant_id"]
                assert extra["role_assignment_id"] == "role_assignment_001"
                assert extra["deleted_by"] == current_user["user_id"]
            finally:
                app.dependency_overrides.clear()


class Test_get_current_user_from_request:
    """get_current_user_from_request関数のテスト"""
    
    def test_get_current_user_正常取得(self):
        """TC-API-R-GCU-001"""
        request = Mock()
        request.headers = {
            "X-User-Id": "user_test_001",
            "X-Tenant-Id": "tenant-test",
        }
        
        result = get_current_user_from_request(request)
        
        assert isinstance(result, dict)
        assert result["user_id"] == "user_test_001"
        assert result["tenant_id"] == "tenant-test"
    
    def test_get_current_user_ヘッダーなし_X_User_Id(self):
        """TC-API-R-GCU-E-001"""
        request = Mock()
        request.headers = {
            "X-Tenant-Id": "tenant-test",
        }
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_from_request(request)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)
    
    def test_get_current_user_ヘッダーなし_X_Tenant_Id(self):
        """TC-API-R-GCU-E-002"""
        request = Mock()
        request.headers = {
            "X-User-Id": "user_test_001",
        }
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_from_request(request)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)
