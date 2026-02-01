"""認証スキーマ"""
from typing import List, Dict
import re
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """ログインリクエスト"""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """ユーザー名の検証"""
        if not re.match(r'^[a-zA-Z0-9_@.\-]+$', v):
            raise ValueError('Username contains invalid characters. Allowed: alphanumeric, _, @, ., -')
        return v


class LoginResponse(BaseModel):
    """ログインレスポンス"""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict


class TokenPayload(BaseModel):
    """トークンペイロード"""

    sub: str  # user_id
    username: str
    tenant_id: str
    roles: List[Dict[str, str]]
    exp: int
    iat: int
    jti: str


class LogoutResponse(BaseModel):
    """ログアウトレスポンス"""

    message: str
