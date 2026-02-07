"""Authentication utilities"""
from pydantic import BaseModel
from typing import List, Optional


class Role(BaseModel):
    """Role model"""
    service_id: str
    service_name: str
    role_code: str
    role_name: str


class JWTPayload(BaseModel):
    """JWT payload model"""
    user_id: str
    tenant_id: str
    roles: List[Role]
    exp: Optional[int] = None
    iat: Optional[int] = None


def has_role(user: JWTPayload, role_codes: List[str]) -> bool:
    """Check if user has any of the specified roles"""
    return any(role.role_code in role_codes for role in user.roles)
