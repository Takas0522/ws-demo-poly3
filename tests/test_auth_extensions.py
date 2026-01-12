"""
Tests for authentication service extensions (Phase 4B-3).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import HTTPException
from app.services.auth import AuthService
from app.schemas import LoginRequest, TenantInfo


@pytest.fixture
def mock_cosmos_db():
    """Mock CosmosDB service."""
    with patch("app.services.auth.cosmos_db") as mock:
        yield mock


@pytest.fixture
def mock_verify_password():
    """Mock password verification."""
    with patch("app.services.auth.verify_password") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def internal_user():
    """Sample internal user."""
    return {
        "id": "user-123",
        "email": "internal@example.com",
        "passwordHash": "$2b$12$hashed",
        "tenantId": "tenant-123",
        "primaryTenantId": "tenant-123",
        "userType": "internal",
        "status": "active",
        "displayName": "Internal User",
        "firstName": "Internal",
        "lastName": "User",
        "roles": ["user"],
        "permissions": ["users.read"],
        "security": {
            "failedLoginAttempts": 0,
            "lockedUntil": None,
            "lastLoginAt": None
        }
    }


@pytest.fixture
def external_user():
    """Sample external user."""
    return {
        "id": "user-456",
        "email": "external@example.com",
        "passwordHash": "$2b$12$hashed",
        "tenantId": "tenant-456",
        "userType": "external",
        "status": "active",
        "displayName": "External User",
        "security": {}
    }


@pytest.fixture
def tenant_users():
    """Sample tenant-users data."""
    return [
        {
            "id": "tu-1",
            "userId": "user-123",
            "tenantId": "tenant-123",
            "tenantName": "Tenant Alpha",
            "roles": ["admin"]
        },
        {
            "id": "tu-2",
            "userId": "user-123",
            "tenantId": "tenant-789",
            "tenantName": "Tenant Beta",
            "roles": ["user"]
        }
    ]


class TestUserTypeValidation:
    """Tests for userType validation during login."""

    @pytest.mark.asyncio
    async def test_external_user_login_rejected(self, mock_cosmos_db, mock_verify_password, external_user):
        """Test that external users cannot login."""
        mock_cosmos_db.find_user_by_email = AsyncMock(return_value=external_user)
        mock_verify_password.return_value = True
        
        request = LoginRequest(
            email="external@example.com",
            password="password123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login(request)
        
        assert exc_info.value.status_code == 401
        assert "管理会社外ユーザーはシステムにログインできません" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_internal_user_login_allowed(self, mock_cosmos_db, mock_verify_password, internal_user, tenant_users):
        """Test that internal users can login."""
        mock_cosmos_db.find_user_by_email = AsyncMock(return_value=internal_user)
        mock_cosmos_db.get_user_tenants = AsyncMock(return_value=tenant_users)
        mock_cosmos_db.update_user_security = AsyncMock()
        mock_cosmos_db.store_refresh_token = AsyncMock()
        mock_verify_password.return_value = True
        
        request = LoginRequest(
            email="internal@example.com",
            password="password123"
        )
        
        response = await AuthService.login(request)
        
        assert response.user.id == "user-123"
        assert response.user.email == "internal@example.com"
        assert response.tokens.access_token is not None
        assert len(response.tenants) == 2


class TestTenantListRetrieval:
    """Tests for tenant list retrieval."""

    @pytest.mark.asyncio
    async def test_login_includes_tenant_list(self, mock_cosmos_db, mock_verify_password, internal_user, tenant_users):
        """Test that login response includes tenant list."""
        mock_cosmos_db.find_user_by_email = AsyncMock(return_value=internal_user)
        mock_cosmos_db.get_user_tenants = AsyncMock(return_value=tenant_users)
        mock_cosmos_db.update_user_security = AsyncMock()
        mock_cosmos_db.store_refresh_token = AsyncMock()
        mock_verify_password.return_value = True
        
        request = LoginRequest(
            email="internal@example.com",
            password="password123"
        )
        
        response = await AuthService.login(request)
        
        assert len(response.tenants) == 2
        assert response.tenants[0].id == "tenant-123"
        assert response.tenants[0].name == "Tenant Alpha"
        assert response.tenants[0].roles == ["admin"]
        assert response.tenants[1].id == "tenant-789"
        assert response.tenants[1].name == "Tenant Beta"

    @pytest.mark.asyncio
    async def test_login_with_no_tenants(self, mock_cosmos_db, mock_verify_password, internal_user):
        """Test login when user has no tenant memberships."""
        mock_cosmos_db.find_user_by_email = AsyncMock(return_value=internal_user)
        mock_cosmos_db.get_user_tenants = AsyncMock(return_value=[])
        mock_cosmos_db.update_user_security = AsyncMock()
        mock_cosmos_db.store_refresh_token = AsyncMock()
        mock_verify_password.return_value = True
        
        request = LoginRequest(
            email="internal@example.com",
            password="password123"
        )
        
        response = await AuthService.login(request)
        
        assert len(response.tenants) == 0


class TestJWTPayloadExtensions:
    """Tests for JWT payload extensions."""

    @pytest.mark.asyncio
    async def test_jwt_contains_tenant_info(self, mock_cosmos_db, mock_verify_password, internal_user, tenant_users):
        """Test that JWT contains tenant information."""
        from app.core.security import decode_token
        
        mock_cosmos_db.find_user_by_email = AsyncMock(return_value=internal_user)
        mock_cosmos_db.get_user_tenants = AsyncMock(return_value=tenant_users)
        mock_cosmos_db.update_user_security = AsyncMock()
        mock_cosmos_db.store_refresh_token = AsyncMock()
        mock_verify_password.return_value = True
        
        request = LoginRequest(
            email="internal@example.com",
            password="password123"
        )
        
        response = await AuthService.login(request)
        token = response.tokens.access_token
        
        payload = decode_token(token)
        
        assert "userType" in payload
        assert payload["userType"] == "internal"
        assert "primaryTenantId" in payload
        assert payload["primaryTenantId"] == "tenant-123"
        assert "selectedTenantId" in payload
        assert payload["selectedTenantId"] == "tenant-123"
        assert "tenants" in payload
        assert len(payload["tenants"]) == 2
        assert payload["tenants"][0]["id"] == "tenant-123"
        assert payload["tenants"][0]["name"] == "Tenant Alpha"


class TestTenantSwitching:
    """Tests for tenant switching functionality."""

    @pytest.mark.asyncio
    async def test_switch_to_valid_tenant(self, mock_cosmos_db):
        """Test switching to a tenant user belongs to."""
        tenant_user = {
            "id": "tu-2",
            "userId": "user-123",
            "tenantId": "tenant-789",
            "tenantName": "Tenant Beta",
            "roles": ["user"]
        }
        
        mock_cosmos_db.get_tenant_user = AsyncMock(return_value=tenant_user)
        
        current_token_data = {
            "sub": "user-123",
            "email": "internal@example.com",
            "displayName": "Internal User",
            "tenantId": "tenant-123",
            "userType": "internal",
            "primaryTenantId": "tenant-123",
            "selectedTenantId": "tenant-123",
            "tenants": [
                {"id": "tenant-123", "name": "Tenant Alpha", "roles": ["admin"]},
                {"id": "tenant-789", "name": "Tenant Beta", "roles": ["user"]}
            ],
            "roles": ["user"],
            "permissions": []
        }
        
        tokens = await AuthService.switch_tenant(
            "user-123",
            "tenant-789",
            current_token_data
        )
        
        assert tokens.access_token is not None
        
        # Decode and verify the new token
        from app.core.security import decode_token
        payload = decode_token(tokens.access_token)
        assert payload["selectedTenantId"] == "tenant-789"
        assert payload["sub"] == "user-123"

    @pytest.mark.asyncio
    async def test_switch_to_invalid_tenant(self, mock_cosmos_db):
        """Test switching to a tenant user doesn't belong to."""
        mock_cosmos_db.get_tenant_user = AsyncMock(return_value=None)
        
        current_token_data = {
            "sub": "user-123",
            "email": "internal@example.com",
            "selectedTenantId": "tenant-123",
            "tenants": [{"id": "tenant-123", "name": "Tenant Alpha", "roles": ["admin"]}]
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.switch_tenant(
                "user-123",
                "tenant-999",
                current_token_data
            )
        
        assert exc_info.value.status_code == 403
        assert "指定されたテナントに所属していません" in exc_info.value.detail


class TestCosmosDBExtensions:
    """Tests for CosmosDB service extensions."""

    @pytest.mark.asyncio
    async def test_get_user_tenants(self):
        """Test retrieving user's tenant memberships."""
        from app.services.cosmosdb import CosmosDBService
        
        service = CosmosDBService()
        mock_container = MagicMock()
        mock_container.query_items.return_value = [
            {"userId": "user-123", "tenantId": "tenant-1", "tenantName": "Tenant 1", "roles": ["admin"]},
            {"userId": "user-123", "tenantId": "tenant-2", "tenantName": "Tenant 2", "roles": ["user"]}
        ]
        
        service.get_tenant_users_container = MagicMock(return_value=mock_container)
        
        result = await service.get_user_tenants("user-123")
        
        assert len(result) == 2
        assert result[0]["tenantId"] == "tenant-1"
        assert result[1]["tenantId"] == "tenant-2"

    @pytest.mark.asyncio
    async def test_get_tenant_user(self):
        """Test retrieving specific tenant-user relationship."""
        from app.services.cosmosdb import CosmosDBService
        
        service = CosmosDBService()
        mock_container = MagicMock()
        mock_container.query_items.return_value = [
            {"userId": "user-123", "tenantId": "tenant-1", "tenantName": "Tenant 1", "roles": ["admin"]}
        ]
        
        service.get_tenant_users_container = MagicMock(return_value=mock_container)
        
        result = await service.get_tenant_user("user-123", "tenant-1")
        
        assert result is not None
        assert result["tenantId"] == "tenant-1"
        assert result["userId"] == "user-123"

    @pytest.mark.asyncio
    async def test_get_tenant_user_not_found(self):
        """Test retrieving non-existent tenant-user relationship."""
        from app.services.cosmosdb import CosmosDBService
        
        service = CosmosDBService()
        mock_container = MagicMock()
        mock_container.query_items.return_value = []
        
        service.get_tenant_users_container = MagicMock(return_value=mock_container)
        
        result = await service.get_tenant_user("user-123", "tenant-999")
        
        assert result is None
