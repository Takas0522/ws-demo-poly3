"""Authentication and authorization dependencies."""

from typing import Optional, Dict, List
from fastapi import Header, HTTPException, status


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """
    Extract and verify JWT token from Authorization header.

    Args:
        authorization: Authorization header value (Bearer token)

    Returns:
        User information from token payload

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "AUTH001", "message": "認証情報が提供されていません"}},
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "AUTH002", "message": "無効なトークンです"}},
        )

    token = parts[1]

    # Verify token using authentication service
    from app.services.authentication_service import authentication_service

    user_info, error_code = await authentication_service.verify_access_token(token)

    if error_code:
        error_messages = {
            "AUTH001": "認証情報が提供されていません",
            "AUTH002": "無効なトークンです",
            "AUTH003": "トークンの有効期限が切れています",
            "AUTH007": "アカウントがロックされています。しばらく経ってから再試行してください",
        }
        error_message = error_messages.get(error_code, "認証に失敗しました")

        status_code_mapping = {
            "AUTH007": status.HTTP_423_LOCKED,
            "AUTH003": status.HTTP_401_UNAUTHORIZED,
            "AUTH002": status.HTTP_401_UNAUTHORIZED,
            "AUTH001": status.HTTP_401_UNAUTHORIZED,
        }
        http_status = status_code_mapping.get(error_code, status.HTTP_401_UNAUTHORIZED)

        raise HTTPException(
            status_code=http_status,
            detail={"error": {"code": error_code, "message": error_message}},
        )

    return user_info


def require_roles(required_roles: List[str], service_id: str = "auth-service"):
    """
    Create a dependency that checks if user has required roles.

    Args:
        required_roles: List of role names that are allowed
        service_id: Service ID to check roles for (default: auth-service)

    Returns:
        Dependency function
    """

    async def check_roles(current_user: Dict = None) -> Dict:
        """
        Check if current user has required roles.

        Args:
            current_user: Current user info from get_current_user

        Returns:
            User information if authorized

        Raises:
            HTTPException: If user doesn't have required roles
        """
        if not current_user:
            # This dependency should be used after get_current_user
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "AUTH001", "message": "認証情報が提供されていません"}},
            )

        # Get user roles for the service
        user_roles = current_user.get("roles", {}).get(service_id, [])

        # Check if user has any of the required roles
        has_required_role = any(role in required_roles for role in user_roles)

        if not has_required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "AUTH_INSUFFICIENT_PERMISSION",
                        "message": "この操作を実行する権限がありません",
                    }
                },
            )

        return current_user

    return check_roles
