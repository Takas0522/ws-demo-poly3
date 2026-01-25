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
