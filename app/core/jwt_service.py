"""JWT token generation and verification service."""
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional
import jwt
from pathlib import Path
from app.core.config import settings


class JWTService:
    """Service for JWT token operations."""
    
    def __init__(self):
        """Initialize JWT service with RSA keys."""
        self._private_key: Optional[str] = None
        self._public_key: Optional[str] = None
        self._load_keys()
    
    def _load_keys(self):
        """Load RSA keys from file system."""
        try:
            private_key_path = Path(settings.jwt_private_key_path)
            public_key_path = Path(settings.jwt_public_key_path)
            
            if private_key_path.exists():
                with open(private_key_path, 'r') as f:
                    self._private_key = f.read()
            
            if public_key_path.exists():
                with open(public_key_path, 'r') as f:
                    self._public_key = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to load JWT keys: {str(e)}")
    
    def generate_access_token(
        self,
        user_id: str,
        name: str,
        tenants: List[Dict[str, any]],
        roles: Dict[str, List[str]]
    ) -> str:
        """
        Generate JWT access token.
        
        Args:
            user_id: User's unique identifier
            name: User's display name
            tenants: List of tenant information (id, name, isPrivileged)
            roles: Dictionary of service roles
            
        Returns:
            JWT access token string
        """
        if not self._private_key:
            raise RuntimeError("Private key not loaded")
        
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "name": name,
            "tenants": tenants,
            "roles": roles,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        }
        
        token = jwt.encode(
            payload,
            self._private_key,
            algorithm=settings.jwt_algorithm
        )
        
        return token
    
    def generate_refresh_token(self, user_id: str) -> str:
        """
        Generate refresh token.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Refresh token string
        """
        if not self._private_key:
            raise RuntimeError("Private key not loaded")
        
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": settings.jwt_issuer,
        }
        
        token = jwt.encode(
            payload,
            self._private_key,
            algorithm=settings.jwt_algorithm
        )
        
        return token
    
    def verify_token(self, token: str) -> Dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        if not self._public_key:
            raise RuntimeError("Public key not loaded")
        
        payload = jwt.decode(
            token,
            self._public_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"verify_exp": True}
        )
        
        return payload


# Global JWT service instance
jwt_service = JWTService()
