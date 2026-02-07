"""FastAPI dependencies"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
from jose import jwt, JWTError

from app.config import get_settings
from app.utils.auth import JWTPayload, Role

settings = get_settings()
security = HTTPBearer()


def verify_jwt_token(token: str) -> Dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> JWTPayload:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    # Convert dict to JWTPayload
    roles = [Role(**role) for role in payload.get("roles", [])]
    
    return JWTPayload(
        user_id=payload["user_id"],
        tenant_id=payload["tenant_id"],
        roles=roles,
        exp=payload.get("exp"),
        iat=payload.get("iat")
    )
