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
        assert user.roles is None
        assert user.tenantIds is None
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

    def test_user_with_embedded_roles_and_tenants(self):
        """Test creating a User with embedded roles and tenantIds."""
        from app.models.user import UserRole as EmbeddedUserRole
        
        user = User(
            id="user-001",
            loginId="admin@example.com",
            name="システム管理者",
            passwordHash="hashed_password",
            isActive=True,
            roles=[
                EmbeddedUserRole(
                    serviceId="auth-service",
                    roleId="role-auth-admin",
                    roleName="全体管理者"
                )
            ],
            tenantIds=["tenant-001"],
        )
        assert user.id == "user-001"
        assert user.roles is not None
        assert len(user.roles) == 1
        assert user.roles[0].serviceId == "auth-service"
        assert user.roles[0].roleId == "role-auth-admin"
        assert user.roles[0].roleName == "全体管理者"
        assert user.tenantIds == ["tenant-001"]


class TestLoginAttemptModel:
    """Test cases for LoginAttempt model."""

    def test_login_attempt_creation(self):
        """Test creating a LoginAttempt instance."""
        attempt = LoginAttempt(
            id="la-001",
            userId="user-001",
            loginId="test@example.com",
            isSuccess=True,
            ipAddress="192.168.1.100",
        )
        assert attempt.id == "la-001"
        assert attempt.userId == "user-001"
        assert attempt.loginId == "test@example.com"
        assert attempt.isSuccess is True
        assert attempt.ipAddress == "192.168.1.100"
        assert isinstance(attempt.attemptedAt, datetime)

    def test_failed_login_attempt(self):
        """Test creating a failed login attempt."""
        attempt = LoginAttempt(
            id="la-002",
            loginId="failed@example.com",
            isSuccess=False,
            ipAddress="192.168.1.101",
        )
        assert attempt.isSuccess is False
        assert attempt.userId is None

    def test_login_attempt_without_user(self):
        """Test creating a login attempt when user is not identified."""
        attempt = LoginAttempt(
            id="la-003",
            loginId="unknown@example.com",
            isSuccess=False,
            ipAddress="192.168.1.102",
        )
        assert attempt.userId is None
        assert attempt.loginId == "unknown@example.com"


class TestUserRoleModel:
    """Test cases for UserRole model."""

    def test_user_role_creation(self):
        """Test creating a UserRole instance."""
        user_role = UserRole(
            id="ur-001",
            userId="user-001",
            roleId="role-auth-admin",
            serviceId="auth-service",
        )
        assert user_role.id == "ur-001"
        assert user_role.userId == "user-001"
        assert user_role.roleId == "role-auth-admin"
        assert user_role.serviceId == "auth-service"
        assert isinstance(user_role.assignedAt, datetime)


class TestUserTenantModel:
    """Test cases for UserTenant model."""

    def test_user_tenant_creation(self):
        """Test creating a UserTenant instance."""
        user_tenant = UserTenant(
            id="ut-001",
            userId="user-001",
            tenantId="tenant-001",
        )
        assert user_tenant.id == "ut-001"
        assert user_tenant.userId == "user-001"
        assert user_tenant.tenantId == "tenant-001"
        assert isinstance(user_tenant.addedAt, datetime)
