"""ロール割り当てモデル"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid


class RoleAssignment(BaseModel):
    """ロール割り当てエンティティ"""

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + "Z"},
    )

    id: str = Field(default_factory=lambda: f"role_assignment_{uuid.uuid4()}")
    tenant_id: str = Field(..., alias="tenantId")
    type: str = "role_assignment"
    user_id: str = Field(..., alias="userId")
    service_id: str = Field(..., alias="serviceId")
    role_name: str = Field(..., alias="roleName")
    assigned_by: str = Field(..., alias="assignedBy")
    assigned_at: datetime = Field(default_factory=datetime.utcnow, alias="assignedAt")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")


class RoleAssignmentCreate(BaseModel):
    """ロール割り当て作成リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(..., alias="tenantId")
    service_id: str = Field(..., alias="serviceId")
    role_name: str = Field(..., alias="roleName")


class Role(BaseModel):
    """ロール情報（参照用）"""

    model_config = ConfigDict(populate_by_name=True)

    service_id: str = Field(..., alias="serviceId")
    role_name: str = Field(..., alias="roleName")
    description: str
