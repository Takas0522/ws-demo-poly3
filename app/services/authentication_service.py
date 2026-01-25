"""Authentication service with business logic."""
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from app.models.user import User
from app.models.login_attempt import LoginAttempt
from app.repositories.user_repository import user_repository
from app.repositories.login_attempt_repository import login_attempt_repository
from app.core.password_service import password_service
from app.core.jwt_service import jwt_service
from app.core.config import settings


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
        token_data = self._generate_tokens(user)
        
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
    
    def _generate_tokens(self, user: User) -> Dict:
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
        
        # Generate refresh token
        refresh_token = jwt_service.generate_refresh_token(user_id=user.id)
        
        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.jwt_access_token_expire_minutes * 60,  # in seconds
            "tokenType": "Bearer"
        }
    
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


# Global service instance
authentication_service = AuthenticationService()
