"""
Example usage of authorization middleware with permission checking.

This module demonstrates how to use the authorization middleware
with FastAPI routes to protect endpoints based on user permissions.
"""
from fastapi import APIRouter, Depends
from app.middleware import (
    get_current_user,
    require_permission,
    require_any_permission,
    require_all_permissions,
)

router = APIRouter(prefix="/api", tags=["examples"])


# Example 1: Single permission requirement
@require_permission("users.read")
@router.get("/users")
async def list_users(current_user: dict = Depends(get_current_user)):
    """
    List all users. Requires 'users.read' permission.
    Admin users can access this endpoint even without the specific permission.
    """
    return {"users": [], "message": "User has 'users.read' permission"}


# Example 2: Single permission without admin override
@require_permission("users.permanent_delete", allow_admin_override=False)
@router.delete("/users/{user_id}/permanent")
async def permanently_delete_user(
    user_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Permanently delete a user. Requires exact permission, even for admins.
    This is useful for highly sensitive operations.
    """
    return {"deleted": True, "user_id": user_id}


# Example 3: Any of multiple permissions
@require_any_permission(["documents.read", "documents.admin", "documents.viewer"])
@router.get("/documents")
async def list_documents(current_user: dict = Depends(get_current_user)):
    """
    List documents. User needs at least ONE of:
    - documents.read
    - documents.admin
    - documents.viewer
    """
    return {"documents": []}


# Example 4: All of multiple permissions
@require_all_permissions(["data.delete", "data.sensitive.access"])
@router.delete("/sensitive-data")
async def delete_sensitive_data(current_user: dict = Depends(get_current_user)):
    """
    Delete sensitive data. User needs ALL of:
    - data.delete
    - data.sensitive.access
    
    This ensures multiple permission requirements are met.
    """
    return {"deleted": True}


# Example 5: Wildcard permissions
@require_permission("users.write")
@router.post("/users")
async def create_user(current_user: dict = Depends(get_current_user)):
    """
    Create a new user. Requires 'users.write' permission.
    
    Note: Users with 'users.*' wildcard permission will also have access.
    """
    return {"created": True}


# Example 6: Nested wildcard permissions
@require_permission("admin.settings.view")
@router.get("/admin/settings/view")
async def view_admin_settings(current_user: dict = Depends(get_current_user)):
    """
    View admin settings. Requires 'admin.settings.view' permission.
    
    Wildcard patterns that would match:
    - admin.settings.*
    - admin.*.view
    - *
    """
    return {"settings": {}}


# Example 7: Programmatic permission check
from app.middleware import has_permission


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get user profile with conditional features based on permissions.
    Demonstrates programmatic permission checking.
    """
    profile = {
        "id": current_user["sub"],
        "email": current_user["email"],
    }
    
    # Check if user can edit profile
    if has_permission(current_user.get("permissions", []), "profile.edit"):
        profile["can_edit"] = True
    else:
        profile["can_edit"] = False
    
    # Check if user can delete account
    if has_permission(current_user.get("permissions", []), "account.delete"):
        profile["can_delete_account"] = True
    else:
        profile["can_delete_account"] = False
    
    return profile


# Example 8: Admin-only endpoint
from app.middleware import is_admin


@router.get("/admin/dashboard")
async def admin_dashboard(current_user: dict = Depends(get_current_user)):
    """
    Admin dashboard. Checks for admin role directly.
    """
    if not is_admin(current_user.get("roles", [])):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return {"dashboard": "admin_data"}


# Example 9: Using permission cache
from app.middleware import permission_cache


@router.post("/permissions/cache/invalidate")
async def invalidate_user_permissions_cache(current_user: dict = Depends(get_current_user)):
    """
    Invalidate cached permissions for the current user.
    Useful after permission changes.
    """
    permission_cache.invalidate(current_user["sub"], current_user["tenantId"])
    return {"message": "Permission cache invalidated"}
