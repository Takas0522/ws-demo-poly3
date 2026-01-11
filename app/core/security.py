"""
Security utilities for password hashing and JWT token handling.
"""
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load RSA keys for RS256
def _load_private_key() -> str:
    """Load RSA private key from file."""
    key_path = settings.jwt_private_key_path
    # Support both absolute and relative paths
    if not os.path.isabs(key_path):
        key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), key_path)
    
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Private key not found at {key_path}")
    
    with open(key_path, "r") as f:
        return f.read()

def _load_public_key() -> str:
    """Load RSA public key from file."""
    key_path = settings.jwt_public_key_path
    # Support both absolute and relative paths
    if not os.path.isabs(key_path):
        key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), key_path)
    
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Public key not found at {key_path}")
    
    with open(key_path, "r") as f:
        return f.read()

# Load keys at module initialization
try:
    if settings.jwt_algorithm == "RS256":
        PRIVATE_KEY = _load_private_key()
        PUBLIC_KEY = _load_public_key()
    else:
        PRIVATE_KEY = settings.jwt_secret
        PUBLIC_KEY = settings.jwt_secret
except Exception as e:
    print(f"Warning: Failed to load RSA keys: {e}")
    print("Falling back to HS256 with jwt_secret")
    PRIVATE_KEY = settings.jwt_secret
    PUBLIC_KEY = settings.jwt_secret


def hash_password(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password(password: str) -> tuple[bool, list[str]]:
    """
    Validate password meets requirements.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    if len(password) < settings.password_min_length:
        errors.append(f"Password must be at least {settings.password_min_length} characters long")
    
    if settings.password_require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if settings.password_require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if settings.password_require_numbers and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if settings.password_require_special_chars and not any(
        c in "!@#$%^&*(),.?\":{}|<>-_+=[]\\;'/`~" for c in password
    ):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.jwt_expires_in)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=settings.jwt_refresh_expires_in)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")
