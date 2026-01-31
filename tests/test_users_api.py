"""Tests for user management API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.user import User, UserRole
from datetime import datetime, UTC


client = TestClient(app)


class TestUserListAPI:
    """Test cases for user list API."""
    
    @patch('app.services.user_service.user_repository')
    def test_list_users_as_admin(self, mock_user_repo):
        """Test listing users as global admin."""
        # Mock users
        mock_users = [
            User(
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
            ),
            User(
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
        ]
        
        mock_user_repo.list_users = AsyncMock(return_value=(mock_users, 2))
        
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
            mock_auth_repo.find_by_id = AsyncMock(return_value=mock_users[0])
            
            # List users
            response = client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 2
        assert data["pagination"]["totalItems"] == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["pageSize"] == 20
    
    @patch('app.services.user_service.user_repository')
    def test_list_users_as_viewer(self, mock_user_repo):
        """Test listing users as viewer."""
        # Mock users
        mock_users = [
            User(
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
        ]
        
        mock_user_repo.list_users = AsyncMock(return_value=(mock_users, 1))
        
        # Generate token for viewer user
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-002",
            name="Viewer User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["閲覧者"]}
        )
        
        # Mock user lookup for verification
        with patch('app.services.authentication_service.user_repository') as mock_auth_repo:
            mock_auth_repo.find_by_id = AsyncMock(return_value=mock_users[0])
            
            # List users
            response = client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 1
    
    def test_list_users_without_auth(self):
        """Test listing users without authentication."""
        response = client.get("/api/users")
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH001"
    
    @patch('app.services.user_service.user_repository')
    def test_list_users_without_required_role(self, mock_user_repo):
        """Test listing users without required role."""
        # Mock user without required role
        mock_user = User(
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
        
        # Generate token for user without role
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-003",
            name="No Role User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={}
        )
        
        # Mock user lookup for verification
        with patch('app.services.authentication_service.user_repository') as mock_auth_repo:
            mock_auth_repo.find_by_id = AsyncMock(return_value=mock_user)
            
            # List users
            response = client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH_INSUFFICIENT_PERMISSION"
    
    @patch('app.services.user_service.user_repository')
    def test_list_users_with_pagination(self, mock_user_repo):
        """Test listing users with pagination."""
        # Mock users
        mock_users = [
            User(
                id=f"user-{i:03d}",
                loginId=f"user{i}@example.com",
                name=f"User {i}",
                passwordHash="$2b$12$xxx",
                isActive=True,
                tenantIds=["tenant-001"],
                roles=[],
                createdAt=datetime.now(UTC),
                updatedAt=datetime.now(UTC)
            )
            for i in range(5)
        ]
        
        mock_user_repo.list_users = AsyncMock(return_value=(mock_users, 50))
        
        # Generate token for admin
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock user lookup
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
            
            # List users with pagination
            response = client.get(
                "/api/users?page=2&pageSize=5",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["pageSize"] == 5
        assert data["pagination"]["totalItems"] == 50
        assert data["pagination"]["totalPages"] == 10
    
    @patch('app.services.user_service.user_repository')
    def test_list_users_with_filters(self, mock_user_repo):
        """Test listing users with filters."""
        # Mock filtered users
        mock_users = [
            User(
                id="user-001",
                loginId="admin@example.com",
                name="Admin User",
                passwordHash="$2b$12$xxx",
                isActive=True,
                tenantIds=["tenant-001"],
                roles=[],
                createdAt=datetime.now(UTC),
                updatedAt=datetime.now(UTC)
            )
        ]
        
        mock_user_repo.list_users = AsyncMock(return_value=(mock_users, 1))
        
        # Generate token
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock user lookup
        with patch('app.services.authentication_service.user_repository') as mock_auth_repo:
            mock_auth_repo.find_by_id = AsyncMock(return_value=mock_users[0])
            
            # List users with filters
            response = client.get(
                "/api/users?name=Admin&isActive=true",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert "Admin" in data["data"][0]["name"]


class TestUserCreateAPI:
    """Test cases for user creation API."""
    
    @patch('app.services.user_service.user_repository')
    def test_create_user_as_admin(self, mock_user_repo):
        """Test creating a user as global admin."""
        # Mock no existing user
        mock_user_repo.find_by_login_id = AsyncMock(return_value=None)
        
        # Mock created user
        created_user = User(
            id="user-new",
            loginId="newuser@example.com",
            name="New User",
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
        
        mock_user_repo.create = AsyncMock(return_value=created_user)
        
        # Generate token for admin
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock user lookup for verification
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
            
            # Create user
            response = client.post(
                "/api/users",
                json={
                    "loginId": "newuser@example.com",
                    "name": "New User",
                    "password": "SecurePass123!",
                    "tenantIds": ["tenant-001"],
                    "roles": [
                        {
                            "serviceId": "auth-service",
                            "roleId": "role-auth-viewer",
                            "roleName": "閲覧者"
                        }
                    ],
                    "isActive": True
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert data["data"]["loginId"] == "newuser@example.com"
        assert data["data"]["name"] == "New User"
        assert data["data"]["isActive"] is True
    
    @patch('app.services.user_service.user_repository')
    def test_create_user_as_viewer(self, mock_user_repo):
        """Test creating a user as viewer (should fail)."""
        # Generate token for viewer
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-002",
            name="Viewer User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["閲覧者"]}
        )
        
        # Mock user lookup
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
            
            # Try to create user
            response = client.post(
                "/api/users",
                json={
                    "loginId": "newuser@example.com",
                    "name": "New User",
                    "password": "SecurePass123!",
                    "isActive": True
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH_INSUFFICIENT_PERMISSION"
    
    def test_create_user_without_auth(self):
        """Test creating a user without authentication."""
        response = client.post(
            "/api/users",
            json={
                "loginId": "newuser@example.com",
                "name": "New User",
                "password": "SecurePass123!",
                "isActive": True
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH001"
    
    @patch('app.services.user_service.user_repository')
    def test_create_user_duplicate_login_id(self, mock_user_repo):
        """Test creating a user with duplicate loginId."""
        # Mock existing user
        existing_user = User(
            id="user-existing",
            loginId="existing@example.com",
            name="Existing User",
            passwordHash="$2b$12$xxx",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[],
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        mock_user_repo.find_by_login_id = AsyncMock(return_value=existing_user)
        
        # Generate token for admin
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock user lookup
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
            
            # Try to create user with duplicate loginId
            response = client.post(
                "/api/users",
                json={
                    "loginId": "existing@example.com",
                    "name": "Duplicate User",
                    "password": "SecurePass123!",
                    "isActive": True
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH_USER_ALREADY_EXISTS"
    
    @patch('app.services.user_service.user_repository')
    def test_create_user_validation_error(self, mock_user_repo):
        """Test creating a user with validation errors."""
        # Generate token for admin
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock user lookup
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
            
            # Try to create user with short password
            response = client.post(
                "/api/users",
                json={
                    "loginId": "newuser@example.com",
                    "name": "New User",
                    "password": "short",  # Too short
                    "isActive": True
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 422
    
    @patch('app.services.user_service.user_repository')
    def test_create_user_password_hashed(self, mock_user_repo):
        """Test that password is hashed when creating a user."""
        # Mock no existing user
        mock_user_repo.find_by_login_id = AsyncMock(return_value=None)
        
        # Track the created user
        created_user_data = {}
        
        async def mock_create(user):
            created_user_data['user'] = user
            return user
        
        mock_user_repo.create = mock_create
        
        # Generate token for admin
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-001",
            name="Admin User",
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Mock user lookup
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
            
            # Create user
            response = client.post(
                "/api/users",
                json={
                    "loginId": "newuser@example.com",
                    "name": "New User",
                    "password": "PlainPassword123!",
                    "isActive": True
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 201
        
        # Verify password was hashed
        if 'user' in created_user_data:
            password_hash = created_user_data['user'].passwordHash
            assert password_hash != "PlainPassword123!"
            assert password_hash.startswith("$2b$12$")
