"""
Authorization middleware and permission checking decorators.
"""
from typing import List, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from app.middleware.auth import get_current_user


# Simple in-memory cache for permissions (Redis integration is future consideration)
class PermissionCache:
    """Simple in-memory cache for user permissions."""
    
    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache with TTL."""
        self._cache: dict = {}
        self._ttl_seconds = ttl_seconds
    
    def get(self, user_id: str, tenant_id: str) -> Optional[List[str]]:
        """Get cached permissions for a user."""
        key = f"{tenant_id}:{user_id}"
        if key in self._cache:
            cached_data = self._cache[key]
            if datetime.utcnow() < cached_data["expires_at"]:
                return cached_data["permissions"]
            else:
                # Expired, remove from cache
                del self._cache[key]
        return None
    
    def set(self, user_id: str, tenant_id: str, permissions: List[str]) -> None:
        """Cache permissions for a user."""
        key = f"{tenant_id}:{user_id}"
        self._cache[key] = {
            "permissions": permissions,
            "expires_at": datetime.utcnow() + timedelta(seconds=self._ttl_seconds)
        }
    
    def invalidate(self, user_id: str, tenant_id: str) -> None:
        """Invalidate cached permissions for a user."""
        key = f"{tenant_id}:{user_id}"
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cached permissions."""
        self._cache.clear()


# Global permission cache instance
permission_cache = PermissionCache()


def has_permission(user_permissions: List[str], required_permission: str) -> bool:
    """
    Check if user has the required permission using dot notation.
    
    Supports wildcard matching:
    - 'users.*' matches 'users.read', 'users.write', etc.
    - 'users.*.delete' matches 'users.profile.delete', 'users.settings.delete', etc.
    - '*' matches any permission
    
    Args:
        user_permissions: List of user's permissions
        required_permission: Required permission in dot notation
    
    Returns:
        True if user has the permission, False otherwise
    """
    # Admin wildcard - has all permissions
    if "*" in user_permissions:
        return True
    
    # Exact match
    if required_permission in user_permissions:
        return True
    
    # Check for wildcard patterns in user permissions
    required_parts = required_permission.split(".")
    
    for user_perm in user_permissions:
        user_parts = user_perm.split(".")
        
        # Check if lengths match or if there's a wildcard
        if len(user_parts) != len(required_parts):
            continue
        
        # Check each part
        match = True
        for user_part, required_part in zip(user_parts, required_parts):
            if user_part != "*" and user_part != required_part:
                match = False
                break
        
        if match:
            return True
    
    return False


def is_admin(user_roles: List[str]) -> bool:
    """
    Check if user has admin role.
    
    Args:
        user_roles: List of user's roles
    
    Returns:
        True if user is an admin
    """
    admin_roles = ["admin", "super_admin", "system_admin"]
    return any(role in admin_roles for role in user_roles)


def require_permission(
    permission: str,
    allow_admin_override: bool = True
) -> Callable:
    """
    Decorator to require specific permission for a route.
    
    Args:
        permission: Required permission in dot notation (e.g., 'users.read')
        allow_admin_override: If True, admin users bypass permission check
    
    Returns:
        Decorator function
    
    Example:
        @router.get("/users")
        @require_permission("users.read")
        async def list_users(current_user: dict = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by FastAPI)
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            user_roles = current_user.get("roles", [])
            user_permissions = current_user.get("permissions", [])
            
            # Admin override
            if allow_admin_override and is_admin(user_roles):
                return await func(*args, **kwargs)
            
            # Check permission
            if not has_permission(user_permissions, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_any_permission(
    permissions: List[str],
    allow_admin_override: bool = True
) -> Callable:
    """
    Decorator to require any of the specified permissions for a route.
    
    Args:
        permissions: List of permissions (user needs at least one)
        allow_admin_override: If True, admin users bypass permission check
    
    Returns:
        Decorator function
    
    Example:
        @router.get("/documents")
        @require_any_permission(["documents.read", "documents.admin"])
        async def list_documents(current_user: dict = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            user_roles = current_user.get("roles", [])
            user_permissions = current_user.get("permissions", [])
            
            # Admin override
            if allow_admin_override and is_admin(user_roles):
                return await func(*args, **kwargs)
            
            # Check if user has any of the required permissions
            if not any(has_permission(user_permissions, perm) for perm in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions. Need one of: {', '.join(permissions)}",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_all_permissions(
    permissions: List[str],
    allow_admin_override: bool = True
) -> Callable:
    """
    Decorator to require all specified permissions for a route.
    
    Args:
        permissions: List of permissions (user needs all of them)
        allow_admin_override: If True, admin users bypass permission check
    
    Returns:
        Decorator function
    
    Example:
        @router.delete("/sensitive-data")
        @require_all_permissions(["data.delete", "data.admin"])
        async def delete_sensitive_data(current_user: dict = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            user_roles = current_user.get("roles", [])
            user_permissions = current_user.get("permissions", [])
            
            # Admin override
            if allow_admin_override and is_admin(user_roles):
                return await func(*args, **kwargs)
            
            # Check if user has all required permissions
            missing_perms = [
                perm for perm in permissions 
                if not has_permission(user_permissions, perm)
            ]
            
            if missing_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(missing_perms)}",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


async def check_permission(
    permission: str,
    current_user: dict = Depends(get_current_user),
    allow_admin_override: bool = True
) -> bool:
    """
    Dependency function to check permission in route handler.
    
    Args:
        permission: Required permission in dot notation
        current_user: Current authenticated user
        allow_admin_override: If True, admin users bypass permission check
    
    Returns:
        True if user has permission
    
    Raises:
        HTTPException: If user doesn't have permission
    
    Example:
        @router.get("/users")
        async def list_users(
            current_user: dict = Depends(get_current_user),
            _: bool = Depends(lambda u=Depends(get_current_user): check_permission("users.read", u))
        ):
            ...
    """
    user_roles = current_user.get("roles", [])
    user_permissions = current_user.get("permissions", [])
    
    # Admin override
    if allow_admin_override and is_admin(user_roles):
        return True
    
    # Check permission
    if not has_permission(user_permissions, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {permission}",
        )
    
    return True
