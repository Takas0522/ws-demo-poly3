"""ユーザー管理API"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from app.schemas.user import UserResponse, UserCreateRequest, UserUpdateRequest
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.models.user import User
from app.dependencies import (
    get_user_service,
    get_auth_service,
    get_current_user_from_token,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def check_tenant_access(
    current_user: User,
    target_tenant_id: str,
    auth_service: AuthService,
) -> None:
    """
    Check tenant isolation access control
    
    Privileged tenants can access all tenant data.
    Regular tenants can only access their own tenant data.
    
    Args:
        current_user: Currently authenticated user
        target_tenant_id: Target tenant ID to access
        auth_service: Authentication service for privilege check
    
    Raises:
        HTTPException: 403 if user attempts to access other tenant's data
    """
    # Check if user's tenant is privileged
    is_privileged = auth_service.is_privileged_tenant(current_user.tenant_id)

    if not is_privileged and current_user.tenant_id != target_tenant_id:
        raise HTTPException(
            status_code=403, detail="Cannot access data from other tenants"
        )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    tenant_id: str = Query(..., description="Tenant ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    current_user: User = Depends(get_current_user_from_token),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> List[UserResponse]:
    """
    List users in a tenant
    
    Requires viewer role or higher (not implemented in Phase 1).
    Privileged tenants can access all tenants; regular tenants can only
    access their own tenant.
    
    Args:
        tenant_id: Target tenant ID
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        current_user: Currently authenticated user (injected)
        user_service: User service (injected)
        auth_service: Authentication service (injected)
    
    Returns:
        List of users in the specified tenant
    
    Raises:
        HTTPException: 403 if accessing other tenant's data without privilege
    """
    # Tenant isolation check
    check_tenant_access(current_user, tenant_id, auth_service)

    # Get user list
    users = await user_service.list_users(tenant_id, skip, limit)

    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            displayName=user.display_name,
            tenantId=user.tenant_id,
            isActive=user.is_active,
            createdAt=user.created_at,
            updatedAt=user.updated_at,
        )
        for user in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: User = Depends(get_current_user_from_token),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Get user details
    
    Args:
        user_id: User ID to retrieve
        tenant_id: Tenant ID
        current_user: Currently authenticated user (injected)
        user_service: User service (injected)
        auth_service: Authentication service (injected)
    
    Returns:
        User details
    
    Raises:
        HTTPException: 403 if accessing other tenant's data, 404 if user not found
    """
    # Tenant isolation check
    check_tenant_access(current_user, tenant_id, auth_service)

    # Get user
    user = await user_service.get_user(user_id, tenant_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        displayName=user.display_name,
        tenantId=user.tenant_id,
        isActive=user.is_active,
        createdAt=user.created_at,
        updatedAt=user.updated_at,
    )


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(get_current_user_from_token),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Create new user
    
    Requires admin role (not implemented in Phase 1).
    
    Args:
        user_data: User creation data
        current_user: Currently authenticated user (injected)
        user_service: User service (injected)
        auth_service: Authentication service (injected)
    
    Returns:
        Created user information
    
    Raises:
        HTTPException: 403 if accessing other tenant, 422 if validation fails
    """
    # Tenant isolation check
    check_tenant_access(current_user, user_data.tenant_id, auth_service)

    try:
        # Create user
        user = await user_service.create_user(user_data, current_user.id)

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            displayName=user.display_name,
            tenantId=user.tenant_id,
            isActive=user.is_active,
            createdAt=user.created_at,
            updatedAt=user.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    user_data: UserUpdateRequest = None,
    current_user: User = Depends(get_current_user_from_token),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Update user
    
    Requires admin role (not implemented in Phase 1).
    
    Args:
        user_id: User ID to update
        tenant_id: Tenant ID
        user_data: User update data
        current_user: Currently authenticated user (injected)
        user_service: User service (injected)
        auth_service: Authentication service (injected)
    
    Returns:
        Updated user information
    
    Raises:
        HTTPException: 403 if accessing other tenant, 422 if validation fails
    """
    # Tenant isolation check
    check_tenant_access(current_user, tenant_id, auth_service)

    try:
        # Update user
        user = await user_service.update_user(
            user_id, tenant_id, user_data, current_user.id
        )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            displayName=user.display_name,
            tenantId=user.tenant_id,
            isActive=user.is_active,
            createdAt=user.created_at,
            updatedAt=user.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: User = Depends(get_current_user_from_token),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Delete user
    
    Requires admin role (not implemented in Phase 1).
    
    Args:
        user_id: User ID to delete
        tenant_id: Tenant ID
        current_user: Currently authenticated user (injected)
        user_service: User service (injected)
        auth_service: Authentication service (injected)
    
    Raises:
        HTTPException: 403 if accessing other tenant
    """
    # Tenant isolation check
    check_tenant_access(current_user, tenant_id, auth_service)

    # Delete user
    await user_service.delete_user(user_id, tenant_id, current_user.id)

    return None
