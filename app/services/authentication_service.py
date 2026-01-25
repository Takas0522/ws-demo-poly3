"""Authentication service with business logic."""
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
import logging
from app.models.user import User
from app.models.login_attempt import LoginAttempt
from app.models.refresh_token import RefreshToken
from app.repositories.user_repository import user_repository
from app.repositories.login_attempt_repository import login_attempt_repository
from app.repositories.refresh_token_repository import refresh_token_repository
from app.core.password_service import password_service
from app.core.jwt_service import jwt_service
from app.core.config import settings


logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service for authentication operations."""
    
    async def authenticate(
        self,
        login_id: str,
        password: str,
        ip_address: str
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Authenticate a user and generate JWT tokens.
        
        Args:
            login_id: User's login identifier
            password: Plain text password
            ip_address: Client IP address
            
        Returns:
            Tuple of (token_data dict, error_message)
            - token_data contains: accessToken, refreshToken, expiresIn
            - error_message is set if authentication fails
        """
        # Find user by login ID
        user = await user_repository.find_by_login_id(login_id)
        
        # Check if account is locked
        if user and user.lockedUntil:
            if datetime.now(UTC) < user.lockedUntil:
                # Account is still locked
                await self._record_login_attempt(
                    login_id=login_id,
                    user_id=user.id if user else None,
                    is_success=False,
                    ip_address=ip_address
                )
                return None, "AUTH007"  # Account locked
            else:
                # Lock period expired, reset
                user.lockedUntil = None
                await user_repository.update(user)
        
        # User not found or inactive
        if not user or not user.isActive:
            await self._record_login_attempt(
                login_id=login_id,
                user_id=user.id if user else None,
                is_success=False,
                ip_address=ip_address
            )
            return None, "AUTH002"  # Invalid credentials
        
        # Verify password
        if not password_service.verify_password(password, user.passwordHash):
            await self._record_login_attempt(
                login_id=login_id,
                user_id=user.id,
                is_success=False,
                ip_address=ip_address
            )
            
            # Check if account should be locked
            await self._check_and_lock_account(user)
            
            return None, "AUTH002"  # Invalid credentials
        
        # Check if user belongs to privileged tenant
        if not self._is_privileged_tenant_user(user):
            await self._record_login_attempt(
                login_id=login_id,
                user_id=user.id,
                is_success=False,
                ip_address=ip_address
            )
            return None, "AUTH006"  # Not privileged tenant user
        
        # Authentication successful - record attempt
        await self._record_login_attempt(
            login_id=login_id,
            user_id=user.id,
            is_success=True,
            ip_address=ip_address
        )
        
        # Generate tokens
        token_data = await self._generate_tokens(user)
        
        return token_data, None
    
    def _is_privileged_tenant_user(self, user: User) -> bool:
        """
        Check if user belongs to a privileged tenant.
        
        Args:
            user: User instance
            
        Returns:
            True if user belongs to privileged tenant
        """
        if not user.tenantIds:
            return False
        
        return settings.privileged_tenant_id in user.tenantIds
    
    async def _generate_tokens(self, user: User) -> Dict:
        """
        Generate JWT access and refresh tokens.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with accessToken, refreshToken, and expiresIn
        """
        # Prepare tenants data for JWT payload
        tenants = []
        if user.tenantIds:
            for tenant_id in user.tenantIds:
                is_privileged = (tenant_id == settings.privileged_tenant_id)
                tenants.append({
                    "id": tenant_id,
                    "name": "特権テナント" if is_privileged else "テナント",
                    "isPrivileged": is_privileged
                })
        
        # Prepare roles data for JWT payload
        roles = {}
        if user.roles:
            for role in user.roles:
                service_id = role.serviceId
                if service_id not in roles:
                    roles[service_id] = []
                roles[service_id].append(role.roleName)
        
        # Generate access token
        access_token = jwt_service.generate_access_token(
            user_id=user.id,
            name=user.name,
            tenants=tenants,
            roles=roles
        )
        
        # Generate refresh token with unique ID
        token_id = f"rt-{uuid4()}"
        refresh_token, expires_at = jwt_service.generate_refresh_token(
            user_id=user.id,
            token_id=token_id
        )
        
        # Store refresh token in database
        # Note: We store the token_id only, not the JWT itself
        # JWT verification is done cryptographically, no need to hash
        try:
            # Store refresh token and wait for completion
            await self._store_refresh_token(
                token_id=token_id,
                user_id=user.id,
                token_hash="",  # Not storing the actual token
                expires_at=expires_at
            )
        except Exception as e:
            # Log error but don't fail login
            logger.error(f"Failed to store refresh token: {str(e)}")
        
        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.jwt_access_token_expire_minutes * 60,  # in seconds
            "tokenType": "Bearer"
        }
    
    async def _store_refresh_token(
        self,
        token_id: str,
        user_id: str,
        token_hash: str,
        expires_at: datetime
    ) -> None:
        """
        Store refresh token in database.
        
        Args:
            token_id: Unique token identifier
            user_id: User ID
            token_hash: Hashed token value
            expires_at: Expiration datetime
        """
        try:
            refresh_token_obj = RefreshToken(
                id=token_id,
                userId=user_id,
                tokenHash=token_hash,
                expiresAt=expires_at,
                isRevoked=False
            )
            await refresh_token_repository.create(refresh_token_obj)
        except Exception as e:
            # Log error but don't fail authentication
            logger.error(f"Failed to store refresh token for user {user_id}: {str(e)}")
    
    async def _record_login_attempt(
        self,
        login_id: str,
        user_id: Optional[str],
        is_success: bool,
        ip_address: str
    ) -> None:
        """
        Record a login attempt.
        
        Args:
            login_id: Login identifier used
            user_id: User ID if identified
            is_success: Whether login was successful
            ip_address: Client IP address
        """
        attempt = LoginAttempt(
            id=f"la-{uuid4()}",
            userId=user_id,
            loginId=login_id,
            isSuccess=is_success,
            ipAddress=ip_address,
            attemptedAt=datetime.now(UTC)
        )
        
        try:
            await login_attempt_repository.create(attempt)
        except Exception:
            # Log but don't fail authentication on logging failure
            pass
    
    async def _check_and_lock_account(self, user: User) -> None:
        """
        Check recent failed attempts and lock account if needed.
        
        Args:
            user: User instance
        """
        # Get recent failed attempts
        failed_attempts = await login_attempt_repository.get_recent_failed_attempts(
            login_id=user.loginId,
            minutes=settings.account_lock_duration_minutes
        )
        
        # Check if max attempts exceeded
        if len(failed_attempts) >= settings.max_login_attempts - 1:
            # Lock the account
            user.lockedUntil = datetime.now(UTC) + timedelta(
                minutes=settings.account_lock_duration_minutes
            )
            await user_repository.update(user)
    
    async def verify_access_token(self, token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Verify access token and check user validity.
        
        Args:
            token: JWT access token string
            
        Returns:
            Tuple of (user_info dict, error_code)
            - Returns (user_info, None) on success
            - Returns (None, error_code) on failure
        """
        # Verify JWT signature and expiration
        payload, error_code = jwt_service.verify_access_token(token)
        if error_code:
            return None, error_code
        
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            return None, "AUTH002"  # Invalid token
        
        # Check if user exists
        user = await user_repository.find_by_id(user_id)
        if not user:
            return None, "AUTH002"  # Invalid token (user doesn't exist)
        
        # Check if user is active
        if not user.isActive:
            return None, "AUTH002"  # Invalid token (user inactive)
        
        # Check if account is locked
        if user.lockedUntil and datetime.now(UTC) < user.lockedUntil:
            return None, "AUTH007"  # Account locked
        
        # Return user info from token
        return {
            "userId": payload.get("sub"),
            "name": payload.get("name"),
            "tenants": payload.get("tenants", []),
            "roles": payload.get("roles", {}),
            "isActive": user.isActive
        }, None
    
    async def refresh_tokens(self, refresh_token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Refresh access token using refresh token (with rotation).
        
        Args:
            refresh_token: JWT refresh token string
            
        Returns:
            Tuple of (token_data dict, error_code)
            - token_data contains: accessToken, refreshToken, expiresIn
            - error_code is set if refresh fails
        """
        # Verify refresh token
        payload, error_code = jwt_service.verify_refresh_token(refresh_token)
        if error_code:
            return None, error_code
        
        # Get user ID and token ID from payload
        user_id = payload.get("sub")
        token_id = payload.get("jti")
        
        if not user_id or not token_id:
            return None, "AUTH002"  # Invalid token
        
        # Check if refresh token exists and is valid
        stored_token = await refresh_token_repository.find_by_id(token_id)
        if not stored_token:
            return None, "AUTH002"  # Invalid token (not found)
        
        # Check if token is revoked
        if stored_token.isRevoked:
            return None, "AUTH002"  # Invalid token (revoked)
        
        # Check if token is already used (rotation check)
        if stored_token.usedAt:
            # Token reuse detected - revoke all tokens for this user
            await refresh_token_repository.revoke_all_for_user(user_id)
            return None, "AUTH002"  # Invalid token (reused)
        
        # Mark token as used and revoke it in a single update
        stored_token.usedAt = datetime.now(UTC)
        stored_token.isRevoked = True
        await refresh_token_repository.update(stored_token)
        
        # Get user
        user = await user_repository.find_by_id(user_id)
        if not user:
            return None, "AUTH002"  # Invalid token (user doesn't exist)
        
        # Check if user is active
        if not user.isActive:
            return None, "AUTH002"  # Invalid token (user inactive)
        
        # Check if account is locked
        if user.lockedUntil and datetime.now(UTC) < user.lockedUntil:
            return None, "AUTH007"  # Account locked
        
        # Generate new tokens
        token_data = await self._generate_tokens(user)
        
        return token_data, None


# Global service instance
authentication_service = AuthenticationService()
