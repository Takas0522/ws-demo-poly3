"""
Authentication service business logic.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas import LoginRequest, LoginResponse, TokenPair, UserProfile, TenantInfo
from app.services.cosmosdb import cosmos_db


class AuthService:
    """Authentication service."""
    
    @staticmethod
    async def login(request: LoginRequest) -> LoginResponse:
        """Authenticate user and generate tokens."""
        # Find user by email
        user = await cosmos_db.find_user_by_email(request.email, request.tenant_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Check if account is locked
        security = user.get("security", {})
        locked_until = security.get("lockedUntil")
        if locked_until:
            locked_date = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
            if locked_date > datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Account is locked until {locked_until}",
                )
        
        # Verify password
        if not verify_password(request.password, user["passwordHash"]):
            await AuthService._handle_failed_login(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Check account status
        if user.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Account is {user.get('status')}",
            )
        
        # Check userType - reject external users
        user_type = user.get("userType", "internal")
        if user_type == "external":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="管理会社外ユーザーはシステムにログインできません",
            )
        
        # Reset failed login attempts
        await AuthService._reset_failed_login_attempts(user["id"], user["tenantId"])
        
        # Get user's tenant memberships
        tenant_users = await cosmos_db.get_user_tenants(user["id"])
        tenant_list = []
        for tu in tenant_users:
            tenant_info = TenantInfo(
                id=tu.get("tenantId", ""),
                name=tu.get("tenantName", ""),
                roles=tu.get("roles", [])
            )
            tenant_list.append(tenant_info)
        
        # Generate tokens with tenant information
        tokens = await AuthService._generate_token_pair(user, tenant_list)
        
        # Update last login
        await cosmos_db.update_user_security(
            user["id"],
            user["tenantId"],
            {"lastLoginAt": datetime.utcnow().isoformat()}
        )
        
        # Return response
        user_profile = UserProfile(
            id=user["id"],
            email=user["email"],
            display_name=user.get("displayName", ""),
            first_name=user.get("firstName"),
            last_name=user.get("lastName"),
            status=user.get("status", "active")
        )
        
        return LoginResponse(tokens=tokens, user=user_profile, tenants=tenant_list)
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> TokenPair:
        """Refresh access token using refresh token."""
        try:
            payload = decode_token(refresh_token)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        user_id = payload.get("sub")
        tenant_id = payload.get("tenantId")
        token_id = payload.get("jti")
        
        # Validate refresh token exists
        if not await cosmos_db.validate_refresh_token(token_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
        
        # Get user
        user = await cosmos_db.find_user_by_id(user_id, tenant_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        if user.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Account is {user.get('status')}",
            )
        
        # Revoke old token and generate new ones
        await cosmos_db.revoke_refresh_token(token_id, user_id)
        
        # Get user's tenant memberships for refresh
        tenant_users = await cosmos_db.get_user_tenants(user_id)
        tenant_list = []
        for tu in tenant_users:
            tenant_info = TenantInfo(
                id=tu.get("tenantId", ""),
                name=tu.get("tenantName", ""),
                roles=tu.get("roles", [])
            )
            tenant_list.append(tenant_info)
        
        tokens = await AuthService._generate_token_pair(user, tenant_list)
        
        return tokens
    
    @staticmethod
    async def logout(user_id: str, refresh_token: Optional[str] = None, all_devices: bool = False) -> None:
        """Logout user by revoking tokens."""
        if all_devices:
            await cosmos_db.revoke_all_refresh_tokens(user_id)
        elif refresh_token:
            try:
                payload = decode_token(refresh_token)
                token_id = payload.get("jti")
                if token_id:
                    await cosmos_db.revoke_refresh_token(token_id, user_id)
            except ValueError:
                pass  # Invalid token, ignore
    
    @staticmethod
    async def switch_tenant(user_id: str, tenant_id: str, current_token_data: Dict[str, Any]) -> TokenPair:
        """Switch user's active tenant."""
        # Verify user has access to the tenant
        tenant_user = await cosmos_db.get_tenant_user(user_id, tenant_id)
        if not tenant_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="指定されたテナントに所属していません",
            )
        
        # Create new token with updated selectedTenantId
        new_token_data = current_token_data.copy()
        new_token_data["selectedTenantId"] = tenant_id
        
        # Create new access token
        access_token = create_access_token({
            k: v for k, v in new_token_data.items() 
            if k not in ["exp", "iat", "iss", "aud", "type"]
        })
        
        # Return token pair (keep same refresh token structure)
        return TokenPair(
            access_token=access_token,
            refresh_token="",  # Client should use existing refresh token
            expires_in=settings.jwt_expires_in,
            token_type="Bearer"
        )
    
    @staticmethod
    async def _generate_token_pair(user: Dict[str, Any], tenants: List[TenantInfo] = None) -> TokenPair:
        """Generate access and refresh token pair."""
        if tenants is None:
            tenants = []
        
        # Get primary tenant ID (default to user's tenantId if not specified)
        primary_tenant_id = user.get("primaryTenantId", user.get("tenantId", ""))
        
        # Create access token with tenant information
        access_token_data = {
            "sub": user["id"],
            "email": user["email"],
            "displayName": user.get("displayName", ""),
            "tenantId": user["tenantId"],
            "userType": user.get("userType", "internal"),
            "primaryTenantId": primary_tenant_id,
            "selectedTenantId": primary_tenant_id,  # Initial value
            "tenants": [{"id": t.id, "name": t.name, "roles": t.roles} for t in tenants],
            "roles": user.get("roles", []),
            "permissions": user.get("permissions", []),
        }
        access_token = create_access_token(access_token_data)
        
        # Create refresh token
        token_id = str(uuid4())
        refresh_token_data = {
            "sub": user["id"],
            "tenantId": user["tenantId"],
            "jti": token_id,
        }
        refresh_token = create_refresh_token(refresh_token_data)
        
        # Store refresh token
        expires_at = datetime.utcnow() + timedelta(seconds=settings.jwt_refresh_expires_in)
        await cosmos_db.store_refresh_token(
            token_id,
            user["id"],
            user["tenantId"],
            refresh_token,
            expires_at.isoformat()
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_expires_in,
            token_type="Bearer"
        )
    
    @staticmethod
    async def _handle_failed_login(user: Dict[str, Any]) -> None:
        """Handle failed login attempt."""
        security = user.get("security", {})
        failed_attempts = security.get("failedLoginAttempts", 0) + 1
        
        updates: Dict[str, Any] = {"failedLoginAttempts": failed_attempts}
        
        if failed_attempts >= settings.max_login_attempts:
            lockout_until = datetime.utcnow() + timedelta(
                minutes=settings.lockout_duration_minutes
            )
            updates["lockedUntil"] = lockout_until.isoformat()
        
        await cosmos_db.update_user_security(user["id"], user["tenantId"], updates)
    
    @staticmethod
    async def _reset_failed_login_attempts(user_id: str, tenant_id: str) -> None:
        """Reset failed login attempts."""
        await cosmos_db.update_user_security(
            user_id,
            tenant_id,
            {"failedLoginAttempts": 0, "lockedUntil": None}
        )


auth_service = AuthService()
