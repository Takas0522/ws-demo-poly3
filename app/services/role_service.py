"""ロール管理サービス"""
from typing import List, Optional
from fastapi import HTTPException
import logging

from app.models.role_assignment import RoleAssignment, RoleAssignmentCreate, Role
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# Phase 1: ハードコードされたロール定義
AUTH_SERVICE_ROLES = [
    {
        "serviceId": "auth-service",
        "roleName": "全体管理者",
        "description": "ユーザー登録・削除、ロール割り当て",
    },
    {
        "serviceId": "auth-service",
        "roleName": "閲覧者",
        "description": "ユーザー情報の参照のみ",
    },
]

TENANT_SERVICE_ROLES = [
    {
        "serviceId": "tenant-management",
        "roleName": "管理者",
        "description": "テナントのCRUD操作",
    },
    {
        "serviceId": "tenant-management",
        "roleName": "閲覧者",
        "description": "テナント情報の参照のみ",
    },
]


class RoleService:
    """ロール管理サービス"""

    def __init__(
        self, role_repository: RoleRepository, user_repository: UserRepository
    ):
        self.role_repository = role_repository
        self.user_repository = user_repository
        self.logger = logger

    def get_available_roles(self) -> List[Role]:
        """
        利用可能なロール一覧取得（Phase 1: ハードコード）
        
        Returns:
            List[Role]: ロール一覧
        
        Note:
            Phase 1ではハードコードされたロール定義を返却。
            Phase 2では各サービスの /api/roles エンドポイントを呼び出して統合。
        """
        all_roles = AUTH_SERVICE_ROLES + TENANT_SERVICE_ROLES
        return [Role(**role) for role in all_roles]

    def validate_role(self, service_id: str, role_name: str) -> bool:
        """
        ロールの妥当性検証
        
        Args:
            service_id: サービスID
            role_name: ロール名
        
        Returns:
            bool: 妥当なロールの場合True
        """
        all_roles = self.get_available_roles()
        return any(
            role.service_id == service_id and role.role_name == role_name
            for role in all_roles
        )

    async def get_user_roles(
        self, user_id: str, tenant_id: str
    ) -> List[RoleAssignment]:
        """
        ユーザーのロール一覧取得
        
        Args:
            user_id: ユーザーID
            tenant_id: テナントID
        
        Returns:
            List[RoleAssignment]: ロール割り当て一覧
        
        Raises:
            HTTPException(404): ユーザーが存在しない場合
        """
        # 1. ユーザーの存在確認
        user = await self.user_repository.get(user_id, tenant_id)
        if not user:
            self.logger.warning(f"User not found: user_id={user_id}, tenant_id={tenant_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ROLE_001_USER_NOT_FOUND",
                    "message": "User not found",
                },
            )

        # 2. ロール割り当て取得
        role_assignments = await self.role_repository.get_by_user_id(user_id, tenant_id)
        return role_assignments

    async def assign_role(
        self, user_id: str, data: RoleAssignmentCreate, assigned_by: str
    ) -> RoleAssignment:
        """
        ユーザーへのロール割り当て
        
        Args:
            user_id: ユーザーID
            data: ロール割り当てデータ
            assigned_by: 割り当て実行者のユーザーID
        
        Returns:
            RoleAssignment: 作成されたロール割り当て
        
        Raises:
            HTTPException(404): ユーザーが存在しない場合
            HTTPException(409): 同じロールが既に割り当て済みの場合
            HTTPException(400): サービスIDまたはロール名が不正な場合
        """
        # 1. ユーザーの存在確認
        user = await self.user_repository.get(user_id, data.tenant_id)
        if not user:
            self.logger.warning(
                f"User not found for role assignment: user_id={user_id}, tenant_id={data.tenant_id}"
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ROLE_001_USER_NOT_FOUND",
                    "message": "User not found",
                },
            )

        # 2. サービスIDとロール名の妥当性確認
        if not self.validate_role(data.service_id, data.role_name):
            self.logger.warning(
                f"Invalid role: service_id={data.service_id}, role_name={data.role_name}"
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ROLE_005_INVALID_ROLE",
                    "message": f"Invalid role '{data.role_name}' for service '{data.service_id}'",
                },
            )

        # 3. 重複チェック付きで作成
        role_assignment, created = await self.role_repository.create_if_not_exists(
            user_id=user_id,
            tenant_id=data.tenant_id,
            service_id=data.service_id,
            role_name=data.role_name,
            assigned_by=assigned_by,
        )

        if not created:
            self.logger.warning(
                f"Role already assigned: user_id={user_id}, service_id={data.service_id}, role_name={data.role_name}"
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "ROLE_002_DUPLICATE_ASSIGNMENT",
                    "message": "Role already assigned to this user",
                },
            )

        self.logger.info(
            f"Role assigned: user_id={user_id}, service_id={data.service_id}, role_name={data.role_name}, assigned_by={assigned_by}"
        )
        return role_assignment

    async def remove_role(
        self, user_id: str, role_assignment_id: str, tenant_id: str
    ) -> None:
        """
        ユーザーからのロール削除
        
        Args:
            user_id: ユーザーID
            role_assignment_id: ロール割り当てID
            tenant_id: テナントID
        
        Raises:
            HTTPException(404): ロール割り当てが存在しない場合
            HTTPException(400): ユーザーIDが一致しない場合
        """
        # 1. ロール割り当ての存在確認
        role_assignment = await self.role_repository.get(role_assignment_id, tenant_id)
        if not role_assignment:
            self.logger.warning(
                f"Role assignment not found: role_assignment_id={role_assignment_id}, tenant_id={tenant_id}"
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ROLE_003_ASSIGNMENT_NOT_FOUND",
                    "message": "Role assignment not found",
                },
            )

        # 2. ユーザーIDの一致確認
        if role_assignment.user_id != user_id:
            self.logger.warning(
                f"User ID mismatch: expected={user_id}, actual={role_assignment.user_id}"
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ROLE_003_ASSIGNMENT_NOT_FOUND",
                    "message": "Role assignment not found for this user",
                },
            )

        # 3. 削除
        await self.role_repository.delete(role_assignment_id, tenant_id)
        self.logger.info(
            f"Role removed: user_id={user_id}, role_assignment_id={role_assignment_id}"
        )
