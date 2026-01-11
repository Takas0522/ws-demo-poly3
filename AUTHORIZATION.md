# Authorization Middleware

This module provides comprehensive authorization middleware for FastAPI with permission checking using dot notation and admin override functionality.

## Features

✅ **Permission Validation**: Validates user permissions using dot notation system (e.g., `users.read`, `documents.write`)
✅ **Route-Level Decorators**: Easy-to-use decorators for protecting routes
✅ **Wildcard Support**: Support for wildcard permissions (`users.*`, `admin.*.view`, `*`)
✅ **Admin Override**: Configurable admin role bypass for permission checks
✅ **Permission Caching**: In-memory caching with TTL for improved performance
✅ **Multiple Permission Patterns**: Support for ANY or ALL permission requirements
✅ **Error Handling**: Clear HTTP 403 errors with detailed permission messages

## Installation

The authorization middleware is part of the auth service. No additional installation required.

## Quick Start

### Basic Usage

```python
from fastapi import APIRouter, Depends
from app.middleware import get_current_user, require_permission

router = APIRouter()

@router.get("/users")
@require_permission("users.read")
async def list_users(current_user: dict = Depends(get_current_user)):
    return {"users": []}
```

### Permission Decorators

#### 1. Single Permission Requirement

```python
@require_permission("users.write")
async def create_user(current_user: dict = Depends(get_current_user)):
    """Requires exact permission or wildcard match (e.g., users.*)"""
    return {"created": True}
```

#### 2. Disable Admin Override

```python
@require_permission("sensitive.delete", allow_admin_override=False)
async def delete_sensitive(current_user: dict = Depends(get_current_user)):
    """Even admins need this specific permission"""
    return {"deleted": True}
```

#### 3. Any Permission (OR logic)

```python
@require_any_permission(["documents.read", "documents.admin"])
async def list_documents(current_user: dict = Depends(get_current_user)):
    """User needs at least ONE of these permissions"""
    return {"documents": []}
```

#### 4. All Permissions (AND logic)

```python
@require_all_permissions(["data.delete", "data.admin"])
async def delete_data(current_user: dict = Depends(get_current_user)):
    """User needs ALL of these permissions"""
    return {"deleted": True}
```

## Permission System

### Dot Notation

Permissions use dot notation for hierarchical structure:
- `users.read` - Read user data
- `users.write` - Create/update users
- `documents.admin.delete` - Admin-level document deletion

### Wildcard Matching

The system supports flexible wildcard patterns:

| User Permission | Grants Access To |
|----------------|------------------|
| `users.*` | `users.read`, `users.write`, `users.delete`, etc. |
| `admin.*.view` | `admin.settings.view`, `admin.users.view`, etc. |
| `*` | ALL permissions (super admin) |

### Admin Roles

Admin roles automatically grant all permissions (unless `allow_admin_override=False`):
- `admin`
- `super_admin`
- `system_admin`

## API Reference

### Decorators

#### `require_permission(permission: str, allow_admin_override: bool = True)`

Requires a specific permission for route access.

**Parameters:**
- `permission`: Required permission in dot notation
- `allow_admin_override`: If True, admin users bypass check

**Raises:**
- `HTTPException(403)`: If user lacks permission

**Example:**
```python
@require_permission("users.read")
async def get_user(current_user: dict = Depends(get_current_user)):
    pass
```

#### `require_any_permission(permissions: List[str], allow_admin_override: bool = True)`

Requires at least one of the specified permissions.

**Parameters:**
- `permissions`: List of acceptable permissions
- `allow_admin_override`: If True, admin users bypass check

**Example:**
```python
@require_any_permission(["docs.read", "docs.admin"])
async def view_docs(current_user: dict = Depends(get_current_user)):
    pass
```

#### `require_all_permissions(permissions: List[str], allow_admin_override: bool = True)`

Requires all specified permissions.

**Parameters:**
- `permissions`: List of required permissions
- `allow_admin_override`: If True, admin users bypass check

**Example:**
```python
@require_all_permissions(["data.delete", "data.admin"])
async def delete_data(current_user: dict = Depends(get_current_user)):
    pass
```

### Utility Functions

#### `has_permission(user_permissions: List[str], required_permission: str) -> bool`

Check if user has a specific permission.

**Example:**
```python
if has_permission(user.permissions, "users.write"):
    # User can write
    pass
```

#### `is_admin(user_roles: List[str]) -> bool`

Check if user has an admin role.

**Example:**
```python
if is_admin(user.roles):
    # User is admin
    pass
```

## Permission Caching

### Overview

The middleware includes an in-memory permission cache to improve performance:
- **TTL**: 5 minutes (300 seconds) by default
- **Scope**: Per user per tenant
- **Invalidation**: Manual invalidation supported

### Using the Cache

```python
from app.middleware import permission_cache

# Cache permissions
permission_cache.set("user-123", "tenant-123", ["users.read", "users.write"])

# Get cached permissions
cached = permission_cache.get("user-123", "tenant-123")

# Invalidate cache
permission_cache.invalidate("user-123", "tenant-123")

# Clear all cache
permission_cache.clear()
```

### Future: Redis Integration

The cache interface is designed for easy Redis integration in the future:
```python
# Future implementation example
from app.middleware import RedisPermissionCache

permission_cache = RedisPermissionCache(
    redis_url="redis://localhost:6379",
    ttl_seconds=300
)
```

## Error Handling

### HTTP 401 - Unauthorized

Thrown when authentication is missing or invalid.

```json
{
  "detail": "Authentication required"
}
```

### HTTP 403 - Forbidden

Thrown when user lacks required permissions.

```json
{
  "detail": "Missing required permission: users.write"
}
```

For multiple permissions:
```json
{
  "detail": "Missing required permissions: data.delete, data.admin"
}
```

## Testing

The middleware includes comprehensive tests:

```bash
# Run all authorization tests
pytest tests/test_authorization.py -v

# Run integration tests
pytest tests/test_authorization_integration.py -v
```

## Examples

See `app/api/examples_authorization.py` for complete working examples covering:
1. Single permission requirements
2. Admin override control
3. Multiple permission patterns
4. Wildcard permissions
5. Programmatic permission checks
6. Cache management

## Security Considerations

### Best Practices

1. **Principle of Least Privilege**: Grant only necessary permissions
2. **Sensitive Operations**: Use `allow_admin_override=False` for critical actions
3. **Regular Audits**: Review and audit permission assignments
4. **Cache Invalidation**: Invalidate cache after permission changes
5. **Wildcard Usage**: Use wildcards judiciously, especially `*`

### Permission Design

```
# Good: Specific permissions
users.read
users.write
users.delete

# Good: Hierarchical structure
admin.settings.view
admin.settings.edit
admin.users.manage

# Use Carefully: Broad wildcards
users.*
admin.*

# Use Very Carefully: Super admin
*
```

## Integration with JWT

Permissions are stored in JWT tokens:

```python
token_payload = {
    "sub": "user-123",
    "email": "user@example.com",
    "tenantId": "tenant-123",
    "roles": ["user"],
    "permissions": ["users.read", "documents.write"]
}
```

The middleware automatically extracts and validates these permissions from the JWT token via the `get_current_user` dependency.

## Migration Guide

### From No Authorization

```python
# Before
@router.get("/users")
async def list_users():
    return {"users": []}

# After
@router.get("/users")
@require_permission("users.read")
async def list_users(current_user: dict = Depends(get_current_user)):
    return {"users": []}
```

### From Role-Based to Permission-Based

```python
# Before (role-based)
if current_user["role"] == "admin":
    # Allow access

# After (permission-based)
if has_permission(current_user["permissions"], "admin.access"):
    # Allow access
```

## Troubleshooting

### Common Issues

**Issue**: 403 Forbidden even with correct permissions
- **Solution**: Check permission cache, try invalidating it
- **Solution**: Verify JWT token includes correct permissions
- **Solution**: Check for typos in permission strings

**Issue**: Admin can't access protected routes
- **Solution**: Verify user has admin role in JWT
- **Solution**: Check if `allow_admin_override=False` is set
- **Solution**: Ensure admin roles include: admin, super_admin, or system_admin

**Issue**: Wildcard permissions not working
- **Solution**: Ensure permission levels match (e.g., `users.*` won't match `users.settings.view`)
- **Solution**: Use appropriate wildcard depth

## Performance Considerations

- **Caching**: Permission checks are cached per user for 5 minutes
- **Decorator Overhead**: Minimal overhead per request
- **Wildcard Matching**: O(n*m) complexity where n = user permissions, m = parts in required permission

## License

MIT
