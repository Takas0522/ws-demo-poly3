"""
Tests for JWT token handling with RS256.
"""
import pytest
from datetime import timedelta
from app.core.security import create_access_token, create_refresh_token, decode_token
from jose import jwt


def test_create_access_token():
    """Test JWT access token creation with RS256."""
    data = {
        "sub": "user-123",
        "email": "test@example.com",
        "tenantId": "tenant-123"
    }
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 100  # RS256 tokens are longer than HS256


def test_create_refresh_token():
    """Test JWT refresh token creation with RS256."""
    data = {
        "sub": "user-123",
        "tenantId": "tenant-123",
        "jti": "token-id-123"
    }
    token = create_refresh_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 100


def test_decode_access_token():
    """Test JWT access token decoding with RS256."""
    data = {
        "sub": "user-123",
        "email": "test@example.com",
        "tenantId": "tenant-123",
        "roles": ["user"],
        "permissions": ["users.read"]
    }
    token = create_access_token(data)
    payload = decode_token(token)
    
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@example.com"
    assert payload["tenantId"] == "tenant-123"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload
    assert "iss" in payload
    assert "aud" in payload


def test_decode_refresh_token():
    """Test JWT refresh token decoding with RS256."""
    data = {
        "sub": "user-123",
        "tenantId": "tenant-123",
        "jti": "token-id-123"
    }
    token = create_refresh_token(data)
    payload = decode_token(token)
    
    assert payload["sub"] == "user-123"
    assert payload["tenantId"] == "tenant-123"
    assert payload["jti"] == "token-id-123"
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    """Test decoding invalid JWT token."""
    with pytest.raises(ValueError, match="Invalid token"):
        decode_token("invalid.token.here")


def test_decode_expired_token():
    """Test decoding expired JWT token."""
    data = {"sub": "user-123"}
    # Create token with negative expiry (already expired)
    token = create_access_token(data, expires_delta=timedelta(seconds=-10))
    
    with pytest.raises(ValueError, match="Invalid token"):
        decode_token(token)


def test_token_with_custom_expiry():
    """Test JWT token with custom expiry time."""
    data = {"sub": "user-123"}
    token = create_access_token(data, expires_delta=timedelta(minutes=30))
    payload = decode_token(token)
    
    assert payload["sub"] == "user-123"
    assert "exp" in payload


def test_token_type_validation():
    """Test that token type is correctly set."""
    access_data = {"sub": "user-123"}
    refresh_data = {"sub": "user-123", "jti": "token-id"}
    
    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(refresh_data)
    
    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_token)
    
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"


def test_token_issuer_and_audience():
    """Test that issuer and audience are correctly set."""
    data = {"sub": "user-123"}
    token = create_access_token(data)
    payload = decode_token(token)
    
    assert payload["iss"] == "saas-auth-service"
    assert payload["aud"] == "saas-app"
