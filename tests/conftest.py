"""pytest設定"""
import pytest
from typing import AsyncGenerator
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """非同期HTTPクライアント"""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sample_user_data():
    """サンプルユーザーデータ"""
    return {
        "username": "testuser@example.com",
        "email": "testuser@example.com",
        "password": "TestP@ssw0rd123",
        "displayName": "テストユーザー",
        "tenantId": "tenant_test",
    }


@pytest.fixture
def sample_login_data():
    """サンプルログインデータ"""
    return {
        "username": "testuser@example.com",
        "password": "TestP@ssw0rd123",
    }


@pytest.fixture
def valid_user_data():
    """有効なユーザーデータ"""
    return {
        "username": "valid.user",
        "email": "valid@example.com",
        "password": "ValidP@ssw0rd123",
        "displayName": "Valid User",
        "tenantId": "tenant-test",
    }


@pytest.fixture
def privileged_tenant_user():
    """特権テナントユーザー"""
    return User(
        id="user_privileged_001",
        tenant_id="tenant_privileged",
        username="admin",
        email="admin@system.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU4g8n.iq7IO",
        display_name="System Admin",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def regular_tenant_user():
    """一般テナントユーザー"""
    return User(
        id="user_regular_001",
        tenant_id="tenant-acme",
        username="john.doe",
        email="john@acme.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU4g8n.iq7IO",
        display_name="John Doe",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def inactive_user():
    """無効化されたユーザー"""
    return User(
        id="user_inactive_001",
        tenant_id="tenant-test",
        username="inactive.user",
        email="inactive@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU4g8n.iq7IO",
        display_name="Inactive User",
        is_active=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# 境界値テストデータ
INVALID_PASSWORDS = [
    "short",                    # 短すぎる
    "nouppercase123!",          # 大文字なし
    "NOLOWERCASE123!",          # 小文字なし
    "NoDigitPassword!",         # 数字なし
    "NoSpecialChar123",         # 特殊文字なし
]

INVALID_EMAILS = [
    "invalid",                  # @なし
    "invalid@",                 # ドメインなし
    "@example.com",             # ローカル部なし
    "invalid@.com",             # 不正なドメイン
]

INVALID_USERNAMES = [
    "ab",                       # 短すぎる
    "a" * 65,                   # 長すぎる
    "user name",                # スペース含む
    "user<script>",             # 不正な文字
]
