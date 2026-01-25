"""Tests for authentication API endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.user import User, UserRole
from datetime import datetime, UTC


client = TestClient(app)


class TestAuthAPI:
    """Test cases for authentication API."""
    
    @patch('app.services.authentication_service.user_repository')
    @patch('app.services.authentication_service.login_attempt_repository')
    def test_login_success(self, mock_login_repo, mock_user_repo):
        """Test successful login."""
        # Mock user with privileged tenant
        mock_user = User(
            id="user-001",
            loginId="admin@example.com",
            name="Test Admin",
            passwordHash="$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",  # Will be mocked
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[
                UserRole(
                    serviceId="auth-service",
                    roleId="role-auth-admin",
                    roleName="全体管理者"
                )
            ]
        )
        
        mock_user_repo.find_by_login_id = AsyncMock(return_value=mock_user)
        mock_login_repo.create = AsyncMock()
        
        # Mock password verification
        with patch('app.services.authentication_service.password_service.verify_password', return_value=True):
            response = client.post(
                "/api/auth/login",
                json={
                    "loginId": "admin@example.com",
                    "password": "correct_password"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert "refreshToken" in data
        assert "expiresIn" in data
        assert data["tokenType"] == "Bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        with patch('app.services.authentication_service.user_repository') as mock_repo:
            mock_repo.find_by_login_id = AsyncMock(return_value=None)
            
            response = client.post(
                "/api/auth/login",
                json={
                    "loginId": "invalid@example.com",
                    "password": "wrong_password"
                }
            )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"]["code"] == "AUTH002"
    
    def test_login_missing_fields(self):
        """Test login with missing required fields."""
        response = client.post(
            "/api/auth/login",
            json={"loginId": "test@example.com"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.authentication_service.user_repository')
    @patch('app.services.authentication_service.login_attempt_repository')
    def test_login_non_privileged_tenant(self, mock_login_repo, mock_user_repo):
        """Test login with non-privileged tenant user."""
        # Mock user without privileged tenant
        mock_user = User(
            id="user-002",
            loginId="user@example.com",
            name="Regular User",
            passwordHash="$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",
            isActive=True,
            tenantIds=["tenant-002"],  # Not privileged tenant
            roles=[]
        )
        
        mock_user_repo.find_by_login_id = AsyncMock(return_value=mock_user)
        mock_login_repo.create = AsyncMock()
        
        with patch('app.services.authentication_service.password_service.verify_password', return_value=True):
            response = client.post(
                "/api/auth/login",
                json={
                    "loginId": "user@example.com",
                    "password": "correct_password"
                }
            )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH006"
    
    @patch('app.services.authentication_service.user_repository')
    @patch('app.services.authentication_service.login_attempt_repository')
    def test_login_locked_account(self, mock_login_repo, mock_user_repo):
        """Test login with locked account."""
        from datetime import timedelta
        
        # Mock locked user
        mock_user = User(
            id="user-003",
            loginId="locked@example.com",
            name="Locked User",
            passwordHash="$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",
            isActive=True,
            lockedUntil=datetime.now(UTC) + timedelta(minutes=30),
            tenantIds=["tenant-001"],
            roles=[]
        )
        
        mock_user_repo.find_by_login_id = AsyncMock(return_value=mock_user)
        mock_login_repo.create = AsyncMock()
        
        response = client.post(
            "/api/auth/login",
            json={
                "loginId": "locked@example.com",
                "password": "any_password"
            }
        )
        
        assert response.status_code == 423
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH007"


class TestVerifyAPI:
    """Test cases for token verification API."""
    
    @patch('app.services.authentication_service.user_repository')
    def test_verify_valid_token(self, mock_user_repo):
        """Test verifying a valid access token."""
        # Create a valid user
        mock_user = User(
            id="user-001",
            loginId="admin@example.com",
            name="Test Admin",
            passwordHash="$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[
                UserRole(
                    serviceId="auth-service",
                    roleId="role-auth-admin",
                    roleName="全体管理者"
                )
            ]
        )
        
        mock_user_repo.find_by_id = AsyncMock(return_value=mock_user)
        
        # Generate a valid token
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id=mock_user.id,
            name=mock_user.name,
            tenants=[{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}],
            roles={"auth-service": ["全体管理者"]}
        )
        
        # Verify the token
        response = client.post(
            "/api/auth/verify",
            json={"token": token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["userId"] == "user-001"
        assert data["name"] == "Test Admin"
        assert data["isActive"] is True
        assert "tenants" in data
        assert "roles" in data
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        response = client.post(
            "/api/auth/verify",
            json={"token": "invalid.token.here"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH002"
    
    @patch('app.services.authentication_service.user_repository')
    def test_verify_token_user_not_found(self, mock_user_repo):
        """Test verifying a token for a non-existent user."""
        # Mock user not found
        mock_user_repo.find_by_id = AsyncMock(return_value=None)
        
        # Generate a token with a user ID
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id="user-nonexistent",
            name="Ghost User",
            tenants=[],
            roles={}
        )
        
        response = client.post(
            "/api/auth/verify",
            json={"token": token}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH002"
    
    @patch('app.services.authentication_service.user_repository')
    def test_verify_token_inactive_user(self, mock_user_repo):
        """Test verifying a token for an inactive user."""
        # Mock inactive user
        mock_user = User(
            id="user-002",
            loginId="inactive@example.com",
            name="Inactive User",
            passwordHash="$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",
            isActive=False,
            tenantIds=["tenant-001"],
            roles=[]
        )
        
        mock_user_repo.find_by_id = AsyncMock(return_value=mock_user)
        
        # Generate a token
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id=mock_user.id,
            name=mock_user.name,
            tenants=[],
            roles={}
        )
        
        response = client.post(
            "/api/auth/verify",
            json={"token": token}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH002"
    
    @patch('app.services.authentication_service.user_repository')
    def test_verify_token_locked_account(self, mock_user_repo):
        """Test verifying a token for a locked account."""
        from datetime import timedelta
        
        # Mock locked user
        mock_user = User(
            id="user-003",
            loginId="locked@example.com",
            name="Locked User",
            passwordHash="$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",
            isActive=True,
            lockedUntil=datetime.now(UTC) + timedelta(minutes=30),
            tenantIds=["tenant-001"],
            roles=[]
        )
        
        mock_user_repo.find_by_id = AsyncMock(return_value=mock_user)
        
        # Generate a token
        from app.core.jwt_service import jwt_service
        token = jwt_service.generate_access_token(
            user_id=mock_user.id,
            name=mock_user.name,
            tenants=[],
            roles={}
        )
        
        response = client.post(
            "/api/auth/verify",
            json={"token": token}
        )
        
        assert response.status_code == 423
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH007"


class TestRefreshAPI:
    """Test cases for token refresh API."""
    
    @patch('app.services.authentication_service.user_repository')
    @patch('app.services.authentication_service.refresh_token_repository')
    def test_refresh_token_success(self, mock_refresh_repo, mock_user_repo):
        """Test refreshing tokens with a valid refresh token."""
        from app.models.refresh_token import RefreshToken
        from datetime import timedelta
        
        # Mock user
        mock_user = User(
            id="user-001",
            loginId="admin@example.com",
            name="Test Admin",
            passwordHash="$2b$12$KIXxLVEz7qGN.QqZ0qZ0qe",
            isActive=True,
            tenantIds=["tenant-001"],
            roles=[
                UserRole(
                    serviceId="auth-service",
                    roleId="role-auth-admin",
                    roleName="全体管理者"
                )
            ]
        )
        
        # Generate refresh token
        from app.core.jwt_service import jwt_service
        token_id = "rt-test-token-id"
        refresh_token, expires_at = jwt_service.generate_refresh_token(
            user_id=mock_user.id,
            token_id=token_id
        )
        
        # Mock stored refresh token
        mock_stored_token = RefreshToken(
            id=token_id,
            userId=mock_user.id,
            tokenHash="hash",
            expiresAt=expires_at,
            isRevoked=False,
            usedAt=None
        )
        
        mock_user_repo.find_by_id = AsyncMock(return_value=mock_user)
        mock_refresh_repo.find_by_id = AsyncMock(return_value=mock_stored_token)
        mock_refresh_repo.update = AsyncMock(return_value=mock_stored_token)
        mock_refresh_repo.create = AsyncMock()
        
        # Refresh tokens
        response = client.post(
            "/api/auth/refresh",
            json={"refreshToken": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert "refreshToken" in data
        assert "expiresIn" in data
        assert data["tokenType"] == "Bearer"
        
        # Verify the stored token was updated
        assert mock_refresh_repo.update.called
    
    def test_refresh_token_invalid(self):
        """Test refreshing with an invalid token."""
        response = client.post(
            "/api/auth/refresh",
            json={"refreshToken": "invalid.token.here"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH002"
    
    @patch('app.services.authentication_service.refresh_token_repository')
    def test_refresh_token_not_found(self, mock_refresh_repo):
        """Test refreshing with a token not in database."""
        # Generate a valid refresh token
        from app.core.jwt_service import jwt_service
        token_id = "rt-nonexistent"
        refresh_token, _ = jwt_service.generate_refresh_token(
            user_id="user-001",
            token_id=token_id
        )
        
        # Mock token not found
        mock_refresh_repo.find_by_id = AsyncMock(return_value=None)
        
        response = client.post(
            "/api/auth/refresh",
            json={"refreshToken": refresh_token}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH002"
    
    @patch('app.services.authentication_service.refresh_token_repository')
    def test_refresh_token_revoked(self, mock_refresh_repo):
        """Test refreshing with a revoked token."""
        from app.models.refresh_token import RefreshToken
        from datetime import timedelta
        
        # Generate refresh token
        from app.core.jwt_service import jwt_service
        token_id = "rt-revoked-token"
        refresh_token, expires_at = jwt_service.generate_refresh_token(
            user_id="user-001",
            token_id=token_id
        )
        
        # Mock revoked token
        mock_stored_token = RefreshToken(
            id=token_id,
            userId="user-001",
            tokenHash="hash",
            expiresAt=expires_at,
            isRevoked=True,  # Token is revoked
            usedAt=None
        )
        
        mock_refresh_repo.find_by_id = AsyncMock(return_value=mock_stored_token)
        
        response = client.post(
            "/api/auth/refresh",
            json={"refreshToken": refresh_token}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH002"
    
    @patch('app.services.authentication_service.refresh_token_repository')
    def test_refresh_token_reuse_detection(self, mock_refresh_repo):
        """Test that token reuse is detected and handled."""
        from app.models.refresh_token import RefreshToken
        from datetime import timedelta
        
        # Generate refresh token
        from app.core.jwt_service import jwt_service
        token_id = "rt-reused-token"
        refresh_token, expires_at = jwt_service.generate_refresh_token(
            user_id="user-001",
            token_id=token_id
        )
        
        # Mock token that was already used
        mock_stored_token = RefreshToken(
            id=token_id,
            userId="user-001",
            tokenHash="hash",
            expiresAt=expires_at,
            isRevoked=False,
            usedAt=datetime.now(UTC) - timedelta(minutes=5)  # Already used
        )
        
        mock_refresh_repo.find_by_id = AsyncMock(return_value=mock_stored_token)
        mock_refresh_repo.revoke_all_for_user = AsyncMock(return_value=1)
        
        response = client.post(
            "/api/auth/refresh",
            json={"refreshToken": refresh_token}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "AUTH002"
        
        # Verify that all tokens for the user were revoked
        mock_refresh_repo.revoke_all_for_user.assert_called_once_with("user-001")
