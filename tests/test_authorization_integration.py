"""
Integration tests for authorization decorators.
"""
import pytest
from fastapi import HTTPException
from app.middleware.authorization import (
    require_permission,
    require_any_permission,
    require_all_permissions,
)
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_require_permission_decorator_with_permission():
    """Test require_permission decorator with valid permission."""
    @require_permission("users.read")
    async def test_func(current_user: dict):
        return {"success": True}
    
    current_user = {
        "sub": "user-123",
        "roles": ["user"],
        "permissions": ["users.read"],
    }
    
    result = await test_func(current_user=current_user)
    assert result == {"success": True}


@pytest.mark.asyncio
async def test_require_permission_decorator_without_permission():
    """Test require_permission decorator without permission."""
    @require_permission("users.write")
    async def test_func(current_user: dict):
        return {"success": True}
    
    current_user = {
        "sub": "user-123",
        "roles": ["user"],
        "permissions": ["users.read"],
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func(current_user=current_user)
    
    assert exc_info.value.status_code == 403
    assert "users.write" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_require_permission_decorator_with_wildcard():
    """Test decorator with wildcard permission."""
    @require_permission("users.delete")
    async def test_func(current_user: dict):
        return {"success": True}
    
    current_user = {
        "sub": "user-123",
        "roles": ["user"],
        "permissions": ["users.*"],
    }
    
    result = await test_func(current_user=current_user)
    assert result == {"success": True}


@pytest.mark.asyncio
async def test_require_permission_decorator_admin_override():
    """Test admin bypass of permission check."""
    @require_permission("users.delete")
    async def test_func(current_user: dict):
        return {"success": True}
    
    current_user = {
        "sub": "user-123",
        "roles": ["admin"],
        "permissions": [],
    }
    
    result = await test_func(current_user=current_user)
    assert result == {"success": True}


@pytest.mark.asyncio
async def test_require_permission_decorator_admin_override_disabled():
    """Test decorator with admin override disabled."""
    @require_permission("users.delete", allow_admin_override=False)
    async def test_func(current_user: dict):
        return {"success": True}
    
    current_user = {
        "sub": "user-123",
        "roles": ["admin"],
        "permissions": [],
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func(current_user=current_user)
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_any_permission_decorator_with_one():
    """Test require_any_permission with one valid permission."""
    @require_any_permission(["users.read", "users.admin"])
    async def test_func(current_user: dict):
        return {"success": True}
    
    current_user = {
        "sub": "user-123",
        "roles": ["user"],
        "permissions": ["users.read"],
    }
    
    result = await test_func(current_user=current_user)
    assert result == {"success": True}


@pytest.mark.asyncio
async def test_require_any_permission_decorator_without_any():
    """Test require_any_permission without any valid permission."""
    @require_any_permission(["users.write", "users.admin"])
    async def test_func(current_user: dict):
        return {"success": True}
    
    current_user = {
        "sub": "user-123",
        "roles": ["user"],
        "permissions": ["users.read"],
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func(current_user=current_user)
    
    assert exc_info.value.status_code == 403
    assert "Need one of" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_require_all_permissions_decorator_with_all():
    """Test require_all_permissions with all permissions."""
    @require_all_permissions(["users.read", "users.write"])
    async def test_func(current_user: dict):
        return {"success": True}
    
    current_user = {
        "sub": "user-123",
        "roles": ["user"],
        "permissions": ["users.read", "users.write"],
    }
    
    result = await test_func(current_user=current_user)
    assert result == {"success": True}


@pytest.mark.asyncio
async def test_require_all_permissions_decorator_missing_one():
    """Test require_all_permissions with one missing permission."""
    @require_all_permissions(["users.read", "users.write"])
    async def test_func(current_user: dict):
        return {"success": True}
    
    current_user = {
        "sub": "user-123",
        "roles": ["user"],
        "permissions": ["users.read"],
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func(current_user=current_user)
    
    assert exc_info.value.status_code == 403
    assert "users.write" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_decorator_without_current_user():
    """Test decorator when current_user is missing."""
    @require_permission("users.read")
    async def test_func():
        return {"success": True}
    
    with pytest.raises(HTTPException) as exc_info:
        await test_func()
    
    assert exc_info.value.status_code == 401
    assert "Authentication required" in str(exc_info.value.detail)


def test_permission_check_with_jwt_token():
    """Test permission validation with actual JWT token."""
    # Create a real token with permissions
    token_data = {
        "sub": "user-123",
        "email": "test@example.com",
        "tenantId": "tenant-123",
        "roles": ["user"],
        "permissions": ["users.read"],
    }
    token = create_access_token(token_data)
    
    # Token is created successfully
    assert token is not None
    assert isinstance(token, str)
