"""Tests for JWT service."""
import pytest
from datetime import datetime, timedelta, UTC
import jwt
from app.core.jwt_service import jwt_service
from app.core.config import settings


class TestJWTService:
    """Test cases for JWT service."""
    
    def test_generate_access_token(self):
        """Test generating an access token."""
        user_id = "user-001"
        name = "Test User"
        tenants = [{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}]
        roles = {"auth-service": ["全体管理者"]}
        
        token = jwt_service.generate_access_token(
            user_id=user_id,
            name=name,
            tenants=tenants,
            roles=roles
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token can be decoded
        payload = jwt_service.verify_token(token)
        assert payload["sub"] == user_id
        assert payload["name"] == name
        assert payload["tenants"] == tenants
        assert payload["roles"] == roles
        assert payload["iss"] == settings.jwt_issuer
        assert payload["aud"] == settings.jwt_audience
    
    def test_generate_refresh_token(self):
        """Test generating a refresh token."""
        user_id = "user-001"
        
        token = jwt_service.generate_refresh_token(user_id=user_id)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token can be decoded (without audience verification for refresh tokens)
        payload = jwt.decode(
            token,
            jwt_service._public_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={"verify_aud": False}
        )
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert payload["iss"] == settings.jwt_issuer
    
    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        user_id = "user-001"
        name = "Test User"
        tenants = [{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}]
        roles = {"auth-service": ["全体管理者"]}
        
        token = jwt_service.generate_access_token(
            user_id=user_id,
            name=name,
            tenants=tenants,
            roles=roles
        )
        
        payload = jwt_service.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["name"] == name
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(jwt.InvalidTokenError):
            jwt_service.verify_token(invalid_token)
    
    def test_token_expiration(self):
        """Test that token includes expiration."""
        user_id = "user-001"
        name = "Test User"
        tenants = [{"id": "tenant-001", "name": "特権テナント", "isPrivileged": True}]
        roles = {"auth-service": ["全体管理者"]}
        
        token = jwt_service.generate_access_token(
            user_id=user_id,
            name=name,
            tenants=tenants,
            roles=roles
        )
        
        payload = jwt_service.verify_token(token)
        
        # Check that exp is set and is in the future
        assert "exp" in payload
        assert "iat" in payload
        
        exp_time = datetime.fromtimestamp(payload["exp"], UTC)
        iat_time = datetime.fromtimestamp(payload["iat"], UTC)
        
        # Expiration should be about 1 hour from issued time
        expected_duration = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        actual_duration = exp_time - iat_time
        
        # Allow for small timing differences
        assert abs(actual_duration.total_seconds() - expected_duration.total_seconds()) < 5
