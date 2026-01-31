"""Role management API endpoints."""

from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user
from app.services.role_service import role_service

router = APIRouter(prefix="/api/roles", tags=["roles"])


# Request/Response models
class RoleResponse(BaseModel):
    """Role response model."""

    id: str = Field(..., description="Role ID")
    serviceId: str = Field(..., description="Service identifier")
    name: str = Field(..., description="Role name")
    description: str = Field(default="", description="Role description")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "role-auth-admin",
                "serviceId": "auth-service",
                "name": "全体管理者",
                "description": "ユーザーの登録・削除を行うことが可能",
            }
        }
    }


class RoleListResponse(BaseModel):
    """Role list response model."""

    data: List[RoleResponse] = Field(..., description="List of roles")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: dict = Field(..., description="Error details")


@router.get(
    "",
    response_model=RoleListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
    },
)
async def list_roles(
    current_user: Dict = Depends(get_current_user),
):
    """
    Get list of available roles.

    Returns all roles that the authenticated user can assign to other users.
    This includes roles from the auth service and potentially from other
    services that the user's tenant has access to.

    Requires authentication. Accessible by users with '全体管理者' (Global Admin)
    or '閲覧者' (Viewer) roles.

    **Role Requirements:**
    - 全体管理者 (Global Admin): ✅
    - 閲覧者 (Viewer): ✅
    """
    # Check if user has required roles (全体管理者 or 閲覧者)
    user_roles = current_user.get("roles", {}).get("auth-service", [])
    has_access = "全体管理者" in user_roles or "閲覧者" in user_roles

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "AUTH_INSUFFICIENT_PERMISSION",
                    "message": "この操作を実行する権限がありません",
                }
            },
        )

    # For MVP, return auth service roles
    # In future, this should:
    # 1. Get all roles from the database
    # 2. Filter based on tenant's available services
    # 3. Include roles from external services via RoleServiceConfig
    roles = await role_service.get_auth_service_roles()

    # Convert to response format
    role_responses = [
        RoleResponse(
            id=role.id,
            serviceId=role.serviceId,
            name=role.name,
            description=role.description,
        )
        for role in roles
    ]

    return RoleListResponse(data=role_responses)


@router.get(
    "/definitions",
    response_model=RoleListResponse,
    responses={
        200: {"description": "List of role definitions from this service"},
    },
)
async def get_role_definitions():
    """
    Get role definitions for external service integration.

    This endpoint is used by the Auth Service to collect role information
    from other services. It does not require authentication as it's meant
    for internal service-to-service communication.

    Returns the roles defined by this auth service that can be assigned
    to users.

    **Note:** This endpoint is for internal use and should be protected
    at the infrastructure level (e.g., internal network only).
    """
    # Return auth service role definitions
    roles = await role_service.get_auth_service_roles()

    # Convert to response format
    role_responses = [
        RoleResponse(
            id=role.id,
            serviceId=role.serviceId,
            name=role.name,
            description=role.description,
        )
        for role in roles
    ]

    return RoleListResponse(data=role_responses)
