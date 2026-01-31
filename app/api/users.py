"""User management API endpoints."""
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator

from app.core.dependencies import get_current_user, require_roles
from app.services.user_service import user_service


router = APIRouter(prefix="/api/users", tags=["users"])


# Request/Response models
class UserRoleInput(BaseModel):
    """User role input model."""
    serviceId: str = Field(..., description="Service identifier")
    roleId: str = Field(..., description="Role identifier")
    roleName: str = Field(..., description="Role name")


class CreateUserRequest(BaseModel):
    """Create user request model."""
    loginId: str = Field(..., min_length=3, max_length=100, description="User's login identifier")
    name: str = Field(..., min_length=1, max_length=100, description="User's display name")
    password: str = Field(..., min_length=8, max_length=100, description="User's password")
    tenantIds: Optional[List[str]] = Field(default=None, description="List of tenant IDs")
    roles: Optional[List[UserRoleInput]] = Field(default=None, description="List of roles")
    isActive: bool = Field(default=True, description="Whether the user account is active")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "loginId": "user@example.com",
                "name": "新規ユーザー",
                "password": "SecurePass123!",
                "tenantIds": ["tenant-001"],
                "roles": [
                    {
                        "serviceId": "auth-service",
                        "roleId": "role-auth-viewer",
                        "roleName": "閲覧者"
                    }
                ],
                "isActive": True
            }
        }
    }


class UserRoleResponse(BaseModel):
    """User role response model."""
    serviceId: str = Field(..., description="Service identifier")
    roleId: str = Field(..., description="Role identifier")
    roleName: str = Field(..., description="Role name")


class UserResponse(BaseModel):
    """User response model."""
    id: str = Field(..., description="User ID")
    loginId: str = Field(..., description="User's login identifier")
    name: str = Field(..., description="User's display name")
    isActive: bool = Field(..., description="Whether the user account is active")
    tenantIds: Optional[List[str]] = Field(default=None, description="List of tenant IDs")
    roles: Optional[List[UserRoleResponse]] = Field(default=None, description="List of roles")
    createdAt: str = Field(..., description="Account creation timestamp")
    updatedAt: str = Field(..., description="Last update timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "user-001",
                "loginId": "admin@example.com",
                "name": "システム管理者",
                "isActive": True,
                "tenantIds": ["tenant-001"],
                "roles": [
                    {
                        "serviceId": "auth-service",
                        "roleId": "role-auth-admin",
                        "roleName": "全体管理者"
                    }
                ],
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z"
            }
        }
    }


class PaginationInfo(BaseModel):
    """Pagination information model."""
    page: int = Field(..., description="Current page number")
    pageSize: int = Field(..., description="Number of items per page")
    totalItems: int = Field(..., description="Total number of items")
    totalPages: int = Field(..., description="Total number of pages")


class UserListResponse(BaseModel):
    """User list response model."""
    data: List[UserResponse] = Field(..., description="List of users")
    pagination: PaginationInfo = Field(..., description="Pagination information")


class UserCreatedResponse(BaseModel):
    """User created response model."""
    data: UserResponse = Field(..., description="Created user information")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: dict = Field(..., description="Error details")


@router.get("", response_model=UserListResponse, responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    403: {"model": ErrorResponse, "description": "Forbidden"}
})
async def list_users(
    page: int = 1,
    pageSize: int = 20,
    sortBy: str = "createdAt",
    sortOrder: str = "desc",
    name: Optional[str] = None,
    loginId: Optional[str] = None,
    isActive: Optional[bool] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get list of users with pagination and filtering.
    
    Requires authentication. Accessible by users with '全体管理者' (Global Admin) 
    or '閲覧者' (Viewer) roles.
    
    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **pageSize**: Items per page (default: 20, max: 100)
    - **sortBy**: Sort field (default: createdAt)
    - **sortOrder**: Sort order - asc/desc (default: desc)
    - **name**: Filter by user name (partial match)
    - **loginId**: Filter by login ID (partial match)
    - **isActive**: Filter by active status (true/false)
    
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
                    "message": "この操作を実行する権限がありません"
                }
            }
        )
    
    # Get users from service
    users, total_count = await user_service.list_users(
        page=page,
        page_size=pageSize,
        sort_by=sortBy,
        sort_order=sortOrder,
        name=name,
        login_id=loginId,
        is_active=isActive
    )
    
    # Convert to response format
    user_responses = []
    for user in users:
        roles_response = None
        if user.roles:
            roles_response = [
                UserRoleResponse(
                    serviceId=role.serviceId,
                    roleId=role.roleId,
                    roleName=role.roleName
                )
                for role in user.roles
            ]
        
        user_responses.append(UserResponse(
            id=user.id,
            loginId=user.loginId,
            name=user.name,
            isActive=user.isActive,
            tenantIds=user.tenantIds,
            roles=roles_response,
            createdAt=user.createdAt.isoformat(),
            updatedAt=user.updatedAt.isoformat()
        ))
    
    # Calculate pagination info
    total_pages = (total_count + pageSize - 1) // pageSize if total_count > 0 else 0
    
    return UserListResponse(
        data=user_responses,
        pagination=PaginationInfo(
            page=page,
            pageSize=pageSize,
            totalItems=total_count,
            totalPages=total_pages
        )
    )


@router.post("", response_model=UserCreatedResponse, status_code=status.HTTP_201_CREATED, responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    403: {"model": ErrorResponse, "description": "Forbidden"},
    409: {"model": ErrorResponse, "description": "Conflict - loginId already exists"},
    422: {"model": ErrorResponse, "description": "Validation error"}
})
async def create_user(
    request: CreateUserRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new user.
    
    Requires authentication and '全体管理者' (Global Admin) role.
    
    **Request Body:**
    - **loginId**: User's login identifier (3-100 characters, unique)
    - **name**: User's display name (1-100 characters)
    - **password**: User's password (8-100 characters, will be hashed with bcrypt cost=12)
    - **tenantIds**: Optional list of tenant IDs the user belongs to
    - **roles**: Optional list of roles to assign
    - **isActive**: Whether the user account is active (default: true)
    
    **Security Features:**
    - Password hashing using bcrypt (cost=12)
    - loginId uniqueness validation
    - Role-based access control
    
    **Role Requirements:**
    - 全体管理者 (Global Admin): ✅
    - 閲覧者 (Viewer): ❌
    """
    # Check if user has 全体管理者 role
    user_roles = current_user.get("roles", {}).get("auth-service", [])
    if "全体管理者" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "AUTH_INSUFFICIENT_PERMISSION",
                    "message": "この操作を実行する権限がありません"
                }
            }
        )
    
    # Convert roles to dict format
    roles_dict = None
    if request.roles:
        roles_dict = [
            {
                "serviceId": role.serviceId,
                "roleId": role.roleId,
                "roleName": role.roleName
            }
            for role in request.roles
        ]
    
    # Create user
    user, error_code = await user_service.create_user(
        login_id=request.loginId,
        name=request.name,
        password=request.password,
        tenant_ids=request.tenantIds,
        roles=roles_dict,
        is_active=request.isActive
    )
    
    # Handle errors
    if error_code:
        if error_code == "AUTH_USER_ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": error_code,
                        "message": "指定されたログインIDは既に使用されています"
                    }
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": error_code,
                        "message": "ユーザーの作成に失敗しました"
                    }
                }
            )
    
    # Convert to response format
    roles_response = None
    if user.roles:
        roles_response = [
            UserRoleResponse(
                serviceId=role.serviceId,
                roleId=role.roleId,
                roleName=role.roleName
            )
            for role in user.roles
        ]
    
    user_response = UserResponse(
        id=user.id,
        loginId=user.loginId,
        name=user.name,
        isActive=user.isActive,
        tenantIds=user.tenantIds,
        roles=roles_response,
        createdAt=user.createdAt.isoformat(),
        updatedAt=user.updatedAt.isoformat()
    )
    
    return UserCreatedResponse(data=user_response)
