"""
Tests for authorization middleware and permission checking.
"""
import pytest
from fastapi import HTTPException
from app.middleware.authorization import (
    has_permission,
    is_admin,
    permission_cache,
    PermissionCache,
)


def test_has_permission_exact_match():
    """Test exact permission match."""
    user_permissions = ["users.read", "users.write", "documents.read"]
    
    assert has_permission(user_permissions, "users.read") is True
    assert has_permission(user_permissions, "users.write") is True
    assert has_permission(user_permissions, "documents.read") is True
    assert has_permission(user_permissions, "users.delete") is False


def test_has_permission_wildcard():
    """Test wildcard permission matching."""
    user_permissions = ["users.*"]
    
    assert has_permission(user_permissions, "users.read") is True
    assert has_permission(user_permissions, "users.write") is True
    assert has_permission(user_permissions, "users.delete") is True
    assert has_permission(user_permissions, "documents.read") is False


def test_has_permission_admin_wildcard():
    """Test admin wildcard permission (all permissions)."""
    user_permissions = ["*"]
    
    assert has_permission(user_permissions, "users.read") is True
    assert has_permission(user_permissions, "documents.write") is True
    assert has_permission(user_permissions, "any.permission.here") is True


def test_has_permission_nested_wildcard():
    """Test nested wildcard permission."""
    user_permissions = ["users.*.delete"]
    
    assert has_permission(user_permissions, "users.profile.delete") is True
    assert has_permission(user_permissions, "users.settings.delete") is True
    assert has_permission(user_permissions, "users.profile.read") is False


def test_has_permission_no_match():
    """Test permission not matched."""
    user_permissions = ["users.read"]
    
    assert has_permission(user_permissions, "users.write") is False
    assert has_permission(user_permissions, "documents.read") is False


def test_has_permission_empty_permissions():
    """Test with empty permissions."""
    user_permissions = []
    
    assert has_permission(user_permissions, "users.read") is False


def test_is_admin_with_admin_role():
    """Test admin role detection."""
    assert is_admin(["admin"]) is True
    assert is_admin(["super_admin"]) is True
    assert is_admin(["system_admin"]) is True
    assert is_admin(["user", "admin"]) is True


def test_is_admin_without_admin_role():
    """Test non-admin role."""
    assert is_admin(["user"]) is False
    assert is_admin(["editor"]) is False
    assert is_admin([]) is False


def test_permission_cache_set_and_get():
    """Test permission cache set and get."""
    cache = PermissionCache()
    permissions = ["users.read", "users.write"]
    
    cache.set("user-123", "tenant-123", permissions)
    cached = cache.get("user-123", "tenant-123")
    
    assert cached == permissions


def test_permission_cache_miss():
    """Test cache miss."""
    cache = PermissionCache()
    cached = cache.get("user-123", "tenant-123")
    
    assert cached is None


def test_permission_cache_invalidate():
    """Test cache invalidation."""
    cache = PermissionCache()
    permissions = ["users.read"]
    
    cache.set("user-123", "tenant-123", permissions)
    assert cache.get("user-123", "tenant-123") == permissions
    
    cache.invalidate("user-123", "tenant-123")
    assert cache.get("user-123", "tenant-123") is None


def test_permission_cache_clear():
    """Test clearing entire cache."""
    cache = PermissionCache()
    
    cache.set("user-1", "tenant-1", ["users.read"])
    cache.set("user-2", "tenant-2", ["documents.read"])
    
    cache.clear()
    
    assert cache.get("user-1", "tenant-1") is None
    assert cache.get("user-2", "tenant-2") is None


def test_permission_cache_expiry():
    """Test cache expiry (TTL)."""
    import time
    cache = PermissionCache(ttl_seconds=1)  # 1 second TTL
    permissions = ["users.read"]
    
    cache.set("user-123", "tenant-123", permissions)
    assert cache.get("user-123", "tenant-123") == permissions
    
    # Wait for cache to expire
    time.sleep(1.1)
    assert cache.get("user-123", "tenant-123") is None


def test_permission_cache_different_tenants():
    """Test cache isolation between tenants."""
    cache = PermissionCache()
    
    cache.set("user-123", "tenant-1", ["users.read"])
    cache.set("user-123", "tenant-2", ["documents.read"])
    
    assert cache.get("user-123", "tenant-1") == ["users.read"]
    assert cache.get("user-123", "tenant-2") == ["documents.read"]


def test_global_permission_cache():
    """Test global permission cache instance."""
    # Clear cache first
    permission_cache.clear()
    
    permissions = ["users.read", "users.write"]
    permission_cache.set("user-456", "tenant-456", permissions)
    
    cached = permission_cache.get("user-456", "tenant-456")
    assert cached == permissions
    
    # Clean up
    permission_cache.clear()


def test_has_permission_complex_patterns():
    """Test complex permission patterns."""
    user_permissions = ["users.*", "documents.read", "admin.*.view"]
    
    # Wildcard matches
    assert has_permission(user_permissions, "users.read") is True
    assert has_permission(user_permissions, "users.write") is True
    assert has_permission(user_permissions, "users.anything") is True
    
    # Exact match
    assert has_permission(user_permissions, "documents.read") is True
    
    # Nested wildcard
    assert has_permission(user_permissions, "admin.settings.view") is True
    assert has_permission(user_permissions, "admin.users.view") is True
    
    # No match
    assert has_permission(user_permissions, "documents.write") is False
    assert has_permission(user_permissions, "admin.settings.edit") is False
