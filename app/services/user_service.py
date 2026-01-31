"""User management service with business logic."""
from datetime import datetime, UTC
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
import logging
from app.models.user import User, UserRole
from app.repositories.user_repository import user_repository
from app.core.password_service import password_service


logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations."""
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        name: Optional[str] = None,
        login_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """
        List users with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page (max 100)
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            name: Filter by name (partial match)
            login_id: Filter by login ID (partial match)
            is_active: Filter by active status
            
        Returns:
            Tuple of (list of users, total count)
        """
        # Validate and sanitize inputs
        page = max(1, page)
        page_size = min(100, max(1, page_size))
        
        # Call repository
        users, total_count = await user_repository.list_users(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            name=name,
            login_id=login_id,
            is_active=is_active
        )
        
        return users, total_count
    
    async def create_user(
        self,
        login_id: str,
        name: str,
        password: str,
        tenant_ids: Optional[List[str]] = None,
        roles: Optional[List[Dict[str, str]]] = None,
        is_active: bool = True
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Create a new user.
        
        Args:
            login_id: User's login identifier
            name: User's display name
            password: Plain text password
            tenant_ids: List of tenant IDs the user belongs to
            roles: List of role dictionaries with serviceId, roleId, roleName
            is_active: Whether the user account is active
            
        Returns:
            Tuple of (User instance, error_code)
            - Returns (user, None) on success
            - Returns (None, error_code) on failure
        """
        # Check if loginId already exists
        existing_user = await user_repository.find_by_login_id(login_id)
        if existing_user:
            return None, "AUTH_USER_ALREADY_EXISTS"
        
        # Hash password
        password_hash = password_service.hash_password(password)
        
        # Convert roles to UserRole objects
        user_roles = None
        if roles:
            user_roles = [
                UserRole(
                    serviceId=role.get("serviceId"),
                    roleId=role.get("roleId"),
                    roleName=role.get("roleName")
                )
                for role in roles
            ]
        
        # Create user object
        user = User(
            id=f"user-{uuid4()}",
            loginId=login_id,
            name=name,
            passwordHash=password_hash,
            isActive=is_active,
            tenantIds=tenant_ids,
            roles=user_roles,
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        
        # Save to database
        try:
            created_user = await user_repository.create(user)
            return created_user, None
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return None, "COMMON_INTERNAL_ERROR"


# Global service instance
user_service = UserService()
