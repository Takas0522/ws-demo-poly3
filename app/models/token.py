"""トークンモデル"""
from typing import List, Dict
from pydantic import BaseModel


class TokenData(BaseModel):
    """JWTトークンのペイロード"""

    user_id: str
    tenant_id: str
    username: str
    roles: List[Dict[str, str]] = []
    exp: int
    iat: int
    jti: str


class TokenResponse(BaseModel):
    """トークンレスポンス"""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict
