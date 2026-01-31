"""Tests for roles API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.user import User, UserRole
from app.models.role import Role
from datetime import datetime, UTC


client = TestClient(app)


class TestRolesListAPI:
    """Test cases for roles list API."""
    
    @patch('app.services.role_service.role_service')
    def test_list_roles_as_admin(self, mock_role_service):
        """Test listing roles as global admin."""
        # Mock roles
        mock_roles = [
            Role(
                id="role-auth-admin",
                serviceId="auth-service",
                name="全体管理者",
                description="ユーザーの登録・削除を行うことが可能"
            ),
            Role(
                id="role-auth-viewer",
                serviceId="auth-service",
                name="閲覧者",
                description="ユーザーの参照のみ可能"
            )
        ]
        
        mock_role_service.get_auth_service_roles = AsyncMock(return_value=mock_roles)
        
        # Generate token for admin user
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock admin user for verification
        admin_user = User(
            id="user-001",
            loginId="admin@example.com",
            name="Admin User",
            passwordHash="$2b$12$xxx",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[
                UserRole(
                    serviceId="auth-service",
                    roleId="role-auth-admin",
                    roleName="全体管理者"
                )
            ],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        with patch('app.services.authentication_service.user_repository') as mock_auth_repo:
            mock_auth_repo.find_by_id = AsyncMock(return_value=admin_user)
            
            # List roles
            response = client.get(
                "/api/roles",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 2
        assert data["data"][0]["name"] == "全体管理者"
        assert data["data"][1]["name"] == "閲覧者"
    
    @patch('app.services.role_service.role_service')
    def test_list_roles_as_viewer(self, mock_role_service):
        """Test listing roles as viewer."""
        # Mock roles
        mock_roles = [
            Role(
                id="role-auth-admin",
                serviceId="auth-service",
                name="全体管理者",
                description="ユーザーの登録・削除を行うことが可能"
            ),
            Role(
                id="role-auth-viewer",
                serviceId="auth-service",
                name="閲覧者",
                description="ユーザーの参照のみ可能"
            )
        ]
        
        mock_role_service.get_auth_service_roles = AsyncMock(return_value=mock_roles)
        
        # Generate token for viewer user
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-002",
            name="Viewer User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["閲覧者"]}
        )
        
        # Mock viewer user for verification
        viewer_user = User(
            id="user-002",
            loginId="viewer@example.com",
            name="Viewer User",
            passwordHash="$2b$12$xxx",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[
                UserRole(
                    serviceId="auth-service",
                    roleId="role-auth-viewer",
                    roleName="閲覧者"
                )
            ],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        with patch('app.services.authentication_service.user_repository') as mock_auth_repo:
            mock_auth_repo.find_by_id = AsyncMock(return_value=viewer_user)
            
            # List roles
            response = client.get(
                "/api/roles",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
    
    def test_list_roles_without_auth(self):
        """Test listing roles without authentication."""
        response = client.get("/api/roles")
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH001"
    
    @patch('app.services.role_service.role_service')
    def test_list_roles_without_permission(self, mock_role_service):
        """Test listing roles without required role."""
        # Generate token for user without role
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-003",
            name="No Role User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={}
        )
        
        # Mock user without role
        no_role_user = User(
            id="user-003",
            loginId="norole@example.com",
            name="No Role User",
            passwordHash="$2b$12$xxx",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        with patch('app.services.authentication_service.user_repository') as mock_auth_repo:
            mock_auth_repo.find_by_id = AsyncMock(return_value=no_role_user)
            
            # Try to list roles
            response = client.get(
                "/api/roles",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH_INSUFFICIENT_PERMISSION"


class TestRolesDefinitionsAPI:
    """Test cases for roles definitions API."""
    
    @patch('app.services.role_service.role_service')
    def test_get_role_definitions(self, mock_role_service):
        """Test getting role definitions (internal endpoint)."""
        # Mock roles
        mock_roles = [
            Role(
                id="role-auth-admin",
                serviceId="auth-service",
                name="全体管理者",
                description="ユーザーの登録・削除を行うことが可能"
            ),
            Role(
                id="role-auth-viewer",
                serviceId="auth-service",
                name="閲覧者",
                description="ユーザーの参照のみ可能"
            )
        ]
        
        mock_role_service.get_auth_service_roles = AsyncMock(return_value=mock_roles)
        
        # Get role definitions (no auth required for internal endpoint)
        response = client.get("/api/roles/definitions")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "role-auth-admin"
        assert data["data"][0]["serviceId"] == "auth-service"
        assert data["data"][0]["name"] == "全体管理者"
        assert data["data"][1]["id"] == "role-auth-viewer"
        assert data["data"][1]["name"] == "閲覧者"
