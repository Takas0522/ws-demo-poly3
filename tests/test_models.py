"""Tests for data models."""
import pytest
from datetime import datetime
from app.models import User, LoginAttempt, UserRole, UserTenant


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self):
        """Test creating a User instance."""
        user = User(
            id="usr_123",
            loginId="test@example.com",
            name="Test User",
            passwordHash="hashed_password",
            isActive=True,
            lockedUntil=None,
        )
        assert user.id == "usr_123"
        assert user.loginId == "test@example.com"
        assert user.name == "Test User"
        assert user.passwordHash == "hashed_password"
        assert user.isActive is True
        assert user.lockedUntil is None
        assert isinstance(user.createdAt, datetime)
        assert isinstance(user.updatedAt, datetime)

    def test_user_with_locked_account(self):
        """Test creating a User with locked account."""
        locked_until = datetime(2024, 12, 31, 23, 59, 59)
        user = User(
            id="usr_456",
            loginId="locked@example.com",
            name="Locked User",
            passwordHash="hashed_password",
            isActive=False,
            lockedUntil=locked_until,
        )
        assert user.isActive is False
        assert user.lockedUntil == locked_until

    def test_user_defaults(self):
        """Test User default values."""
        user = User(
            id="usr_789",
            loginId="default@example.com",
            name="Default User",
            passwordHash="hashed_password",
        )
        assert user.isActive is True
        assert user.lockedUntil is None


class TestLoginAttemptModel:
    """Test cases for LoginAttempt model."""

    def test_login_attempt_creation(self):
        """Test creating a LoginAttempt instance."""
        attempt = LoginAttempt(
            id="att_123",
            loginId="test@example.com",
            isSuccess=True,
            ipAddress="192.168.1.100",
            userAgent="Mozilla/5.0",
        )
        assert attempt.id == "att_123"
        assert attempt.loginId == "test@example.com"
        assert attempt.isSuccess is True
        assert attempt.ipAddress == "192.168.1.100"
        assert attempt.userAgent == "Mozilla/5.0"
        assert isinstance(attempt.attemptedAt, datetime)

    def test_failed_login_attempt(self):
        """Test creating a failed login attempt."""
        attempt = LoginAttempt(
            id="att_456",
            loginId="failed@example.com",
            isSuccess=False,
        )
        assert attempt.isSuccess is False
        assert attempt.ipAddress is None
        assert attempt.userAgent is None


class TestUserRoleModel:
    """Test cases for UserRole model."""

    def test_user_role_creation(self):
        """Test creating a UserRole instance."""
        user_role = UserRole(
            id="usr_123_role_admin",
            userId="usr_123",
            roleId="role_admin",
            serviceId="srv_auth",
        )
        assert user_role.id == "usr_123_role_admin"
        assert user_role.userId == "usr_123"
        assert user_role.roleId == "role_admin"
        assert user_role.serviceId == "srv_auth"


class TestUserTenantModel:
    """Test cases for UserTenant model."""

    def test_user_tenant_creation(self):
        """Test creating a UserTenant instance."""
        user_tenant = UserTenant(
            id="usr_123_tenant_priv",
            userId="usr_123",
            tenantId="tnt_privileged",
        )
        assert user_tenant.id == "usr_123_tenant_priv"
        assert user_tenant.userId == "usr_123"
        assert user_tenant.tenantId == "tnt_privileged"
