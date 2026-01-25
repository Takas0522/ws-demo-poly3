"""JWT token generation and verification service."""
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Tuple
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
    
    def generate_refresh_token(self, user_id: str, token_id: str) -> Tuple[str, datetime]:
        """
        Generate refresh token with token ID for rotation support.
        
        Args:
            user_id: User's unique identifier
            token_id: Unique token identifier for tracking
            
        Returns:
            Tuple of (refresh token string, expiration datetime)
        """
        if not self._private_key:
            raise RuntimeError("Private key not loaded")
        
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "jti": token_id,  # JWT ID for tracking
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
        
        return token, expires_at
    
    def verify_token(self, token: str, verify_audience: bool = True) -> Dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            verify_audience: Whether to verify audience (False for refresh tokens)
            
        Returns:
            Decoded token payload
            
        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        if not self._public_key:
            raise RuntimeError("Public key not loaded")
        
        # Set options for audience verification
        options = {"verify_exp": True}
        if not verify_audience:
            options["verify_aud"] = False
        
        # Build decode parameters
        decode_params = {
            "jwt": token,
            "key": self._public_key,
            "algorithms": [settings.jwt_algorithm],
            "issuer": settings.jwt_issuer,
            "options": options
        }
        
        # Add audience only if we're verifying it
        if verify_audience:
            decode_params["audience"] = settings.jwt_audience
        
        payload = jwt.decode(**decode_params)
        
        return payload
    
    def verify_access_token(self, token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Verify access token and return payload or error code.
        
        Args:
            token: JWT access token string
            
        Returns:
            Tuple of (payload dict, error_code)
            - Returns (payload, None) on success
            - Returns (None, error_code) on failure
        """
        try:
            payload = self.verify_token(token, verify_audience=True)
            
            # Check if it's a refresh token (should not be used as access token)
            if payload.get("type") == "refresh":
                return None, "AUTH002"  # Invalid token
            
            return payload, None
            
        except jwt.ExpiredSignatureError:
            return None, "AUTH003"  # Token expired
        except jwt.InvalidTokenError:
            return None, "AUTH002"  # Invalid token
        except Exception:
            return None, "AUTH002"  # Invalid token
    
    def verify_refresh_token(self, token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Verify refresh token and return payload or error code.
        
        Args:
            token: JWT refresh token string
            
        Returns:
            Tuple of (payload dict, error_code)
            - Returns (payload, None) on success
            - Returns (None, error_code) on failure
        """
        try:
            payload = self.verify_token(token, verify_audience=False)
            
            # Check if it's actually a refresh token
            if payload.get("type") != "refresh":
                return None, "AUTH002"  # Invalid token
            
            return payload, None
            
        except jwt.ExpiredSignatureError:
            return None, "AUTH003"  # Token expired
        except jwt.InvalidTokenError:
            return None, "AUTH002"  # Invalid token
        except Exception:
            return None, "AUTH002"  # Invalid token


# Global JWT service instance
jwt_service = JWTService()
