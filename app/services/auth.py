"""
Authentication service business logic.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
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
from app.schemas import LoginRequest, LoginResponse, TokenPair, UserProfile
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
        
        # Reset failed login attempts
        await AuthService._reset_failed_login_attempts(user["id"], user["tenantId"])
        
        # Generate tokens
        tokens = await AuthService._generate_token_pair(user)
        
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
        
        return LoginResponse(tokens=tokens, user=user_profile)
    
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
        tokens = await AuthService._generate_token_pair(user)
        
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
    async def _generate_token_pair(user: Dict[str, Any]) -> TokenPair:
        """Generate access and refresh token pair."""
        # Create access token
        access_token_data = {
            "sub": user["id"],
            "email": user["email"],
            "displayName": user.get("displayName", ""),
            "tenantId": user["tenantId"],
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
