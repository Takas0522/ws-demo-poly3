"""ユーザースキーマ"""
from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class UserResponse(BaseModel):
    """ユーザーレスポンス"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    username: str
    email: EmailStr
    display_name: str = Field(..., alias="displayName")
    tenant_id: str = Field(..., alias="tenantId")
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class UserCreateRequest(BaseModel):
    """ユーザー作成リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    display_name: str = Field(..., alias="displayName", min_length=1, max_length=100)
    tenant_id: str = Field(..., alias="tenantId", min_length=1, max_length=64)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """ユーザー名の検証"""
        if not re.match(r'^[a-zA-Z0-9_@.\-]+$', v):
            raise ValueError('Username contains invalid characters. Allowed: alphanumeric, _, @, ., -')
        return v
    
    @field_validator('tenant_id')
    @classmethod
    def validate_tenant_id(cls, v: str) -> str:
        """テナントIDの検証"""
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('Tenant ID contains invalid characters. Allowed: alphanumeric, _, -')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """パスワードの複雑性検証"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[^a-zA-Z0-9]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdateRequest(BaseModel):
    """ユーザー更新リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    display_name: Optional[str] = Field(None, alias="displayName")
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = Field(None, alias="isActive")
