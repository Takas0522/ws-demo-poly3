"""Tests for user edit API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.user import User, UserRole
from datetime import datetime, UTC


client = TestClient(app)


class TestUserGetAPI:
    """Test cases for user get API."""
    
    @patch('app.services.user_service.user_repository')
    def test_get_user_as_admin(self, mock_user_repo):
        """Test getting a user as global admin."""
        # Mock user
        mock_user = User(
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
        
        mock_user_repo.find_by_id = AsyncMock(return_value=mock_user)
        
        # Generate token for admin user
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock user lookup for verification
        with patch('app.services.authentication_service.user_repository') as mock_auth_repo:
            mock_auth_repo.find_by_id = AsyncMock(return_value=mock_user)
            
            # Get user
            response = client.get(
                "/api/users/user-001",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user-001"
        assert data["loginId"] == "admin@example.com"
        assert data["name"] == "Admin User"
        assert data["isActive"] is True
    
    @patch('app.services.user_service.user_repository')
    def test_get_user_not_found(self, mock_user_repo):
        """Test getting a non-existent user."""
        # Mock no user found
        mock_user_repo.find_by_id = AsyncMock(return_value=None)
        
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
            
            # Try to get non-existent user
            response = client.get(
                "/api/users/user-999",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH_USER_NOT_FOUND"


class TestUserUpdateAPI:
    """Test cases for user update API."""
    
    @patch('app.services.user_service.user_repository')
    def test_update_user_name(self, mock_user_repo):
        """Test updating user name."""
        # Mock existing user
        existing_user = User(
            id="user-002",
            loginId="user@example.com",
            name="Original Name",
            passwordHash="$2b$12$xxx",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        # Mock updated user
        updated_user = User(
            id="user-002",
            loginId="user@example.com",
            name="Updated Name",
            passwordHash="$2b$12$xxx",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        mock_user_repo.find_by_id = AsyncMock(return_value=existing_user)
        mock_user_repo.update = AsyncMock(return_value=updated_user)
        
        # Generate token for admin
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
            
            # Update user
            response = client.put(
                "/api/users/user-002",
                json={"name": "Updated Name"},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
    
    @patch('app.services.user_service.user_repository')
    def test_update_user_password(self, mock_user_repo):
        """Test updating user password."""
        # Mock existing user
        existing_user = User(
            id="user-002",
            loginId="user@example.com",
            name="Test User",
            passwordHash="$2b$12$oldpassword",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        # Mock updated user (password will be changed)
        updated_user = User(
            id="user-002",
            loginId="user@example.com",
            name="Test User",
            passwordHash="$2b$12$newpassword",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        mock_user_repo.find_by_id = AsyncMock(return_value=existing_user)
        mock_user_repo.update = AsyncMock(return_value=updated_user)
        
        # Generate token for admin
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock admin user
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
            
            # Update user password
            response = client.put(
                "/api/users/user-002",
                json={"password": "NewSecurePass123!"},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
    
    @patch('app.services.user_service.user_repository')
    def test_update_user_active_status(self, mock_user_repo):
        """Test toggling user active status."""
        # Mock existing user
        existing_user = User(
            id="user-002",
            loginId="user@example.com",
            name="Test User",
            passwordHash="$2b$12$xxx",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        # Mock updated user (inactive)
        updated_user = User(
            id="user-002",
            loginId="user@example.com",
            name="Test User",
            passwordHash="$2b$12$xxx",
            isActive=False,
            tenantIds=["tenant-001"],
            roles=[],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        mock_user_repo.find_by_id = AsyncMock(return_value=existing_user)
        mock_user_repo.update = AsyncMock(return_value=updated_user)
        
        # Generate token for admin
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock admin user
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
            
            # Deactivate user
            response = client.put(
                "/api/users/user-002",
                json={"isActive": False},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["isActive"] is False
    
    @patch('app.services.user_service.user_repository')
    def test_update_user_without_permission(self, mock_user_repo):
        """Test updating user without admin permission."""
        # Generate token for viewer (no admin role)
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-002",
            name="Viewer User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["閲覧者"]}
        )
        
        # Mock viewer user
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
            
            # Try to update user
            response = client.put(
                "/api/users/user-003",
                json={"name": "Updated Name"},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH_INSUFFICIENT_PERMISSION"


class TestUserRolesUpdateAPI:
    """Test cases for user roles update API."""
    
    @patch('app.services.user_service.user_repository')
    def test_update_user_roles(self, mock_user_repo):
        """Test updating user roles."""
        # Mock existing user
        existing_user = User(
            id="user-002",
            loginId="user@example.com",
            name="Test User",
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
        
        # Mock updated user with new roles
        updated_user = User(
            id="user-002",
            loginId="user@example.com",
            name="Test User",
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
        
        mock_user_repo.find_by_id = AsyncMock(return_value=existing_user)
        mock_user_repo.update = AsyncMock(return_value=updated_user)
        
        # Generate token for admin
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock admin user
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
            
            # Update user roles
            response = client.put(
                "/api/users/user-002/roles",
                json={
                    "roles": [
                        {
                            "serviceId": "auth-service",
                            "roleId": "role-auth-admin",
                            "roleName": "全体管理者"
                        }
                    ]
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["roles"]) == 1
        assert data["roles"][0]["roleName"] == "全体管理者"
