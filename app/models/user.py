"""ユーザーモデル"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
import uuid


class User(BaseModel):
    """ユーザーエンティティ"""

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + "Z"},
    )

    id: str = Field(default_factory=lambda: f"user_{uuid.uuid4()}")
    tenant_id: str = Field(..., alias="tenantId")
    type: str = "user"
    username: str
    email: EmailStr
    password_hash: str = Field(..., alias="passwordHash")
    display_name: str = Field(..., alias="displayName")
    is_active: bool = Field(default=True, alias="isActive")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    created_by: Optional[str] = Field(None, alias="createdBy")
    updated_by: Optional[str] = Field(None, alias="updatedBy")


class UserCreate(BaseModel):
    """ユーザー作成リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    username: str
    email: EmailStr
    password: str
    display_name: str = Field(..., alias="displayName")
    tenant_id: str = Field(..., alias="tenantId")


class UserUpdate(BaseModel):
    """ユーザー更新リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    display_name: Optional[str] = Field(None, alias="displayName")
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = Field(None, alias="isActive")
