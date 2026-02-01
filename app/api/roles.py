"""ロール管理API"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request
import logging

from app.models.role_assignment import RoleAssignment, RoleAssignmentCreate, Role
from app.models.user import User
from app.services.role_service import RoleService
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter()


def get_role_service(request: Request) -> RoleService:
    """ロールサービスの依存性注入"""
    container = request.app.state.cosmos_container
    role_repository = RoleRepository(container)
    user_repository = UserRepository(container)
    return RoleService(role_repository, user_repository)


def get_current_user_from_request(request: Request) -> dict:
    """
    リクエストから現在のユーザー情報を取得（簡易実装）
    
    Note:
        Phase 1では簡易実装。Phase 2で共通ライブラリのget_current_userを使用。
    """
    # TODO: Phase 2で共通ライブラリの認証ミドルウェア、get_current_userを使用
    # 現時点ではヘッダーからユーザー情報を取得する簡易実装
    user_id = request.headers.get("X-User-Id")
    tenant_id = request.headers.get("X-Tenant-Id")
    
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
    }


@router.get("/roles", response_model=dict)
async def get_available_roles(
    role_service: RoleService = Depends(get_role_service),
) -> dict:
    """
    利用可能なロール一覧取得
    
    Returns:
        dict: ロール一覧（data配列形式）
    
    Business Logic:
        1. Phase 1では、ハードコードされたロール定義を返却
        2. Phase 2では、各サービスの /api/roles エンドポイントを呼び出して統合
    
    Performance:
        - 応答時間: < 200ms (P95)
    """
    roles = role_service.get_available_roles()
    return {"data": [role.model_dump(by_alias=True) for role in roles]}


@router.get("/users/{user_id}/roles", response_model=dict)
async def get_user_roles(
    user_id: str,
    tenant_id: str,
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user_from_request),
) -> dict:
    """
    ユーザーロール一覧取得
    
    Args:
        user_id: ユーザーID
        tenant_id: テナントID（クエリパラメータ）
        
    Returns:
        dict: ロール割り当て一覧（data配列形式）
    
    Authorization:
        閲覧者以上（Phase 2で実装）
    
    Business Logic:
        1. ユーザーの存在確認
        2. テナント分離チェック（特権テナント以外は自テナントのみ）
        3. Cosmos DBから該当ユーザーのRoleAssignmentを検索
    
    Performance:
        - 応答時間: < 200ms (P95)
    """
    # テナント分離チェック（簡易実装）
    # TODO: Phase 2で共通ライブラリのrequire_roleを使用
    if current_user["tenant_id"] != tenant_id:
        # 特権テナントでない場合は自テナントのみ
        # TODO: 特権テナントチェックを追加
        logger.warning(
            f"Cross-tenant access attempt: user_tenant={current_user['tenant_id']}, requested_tenant={tenant_id}"
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "ROLE_006_TENANT_ISOLATION_VIOLATION",
                "message": "Cannot access user in different tenant",
            },
        )

    role_assignments = await role_service.get_user_roles(user_id, tenant_id)
    return {
        "data": [ra.model_dump(by_alias=True) for ra in role_assignments]
    }


@router.post("/users/{user_id}/roles", response_model=dict, status_code=201)
async def assign_role(
    user_id: str,
    data: RoleAssignmentCreate,
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user_from_request),
) -> dict:
    """
    ユーザーへのロール割り当て
    
    Args:
        user_id: ユーザーID（パスパラメータ）
        data: ロール割り当てデータ（リクエストボディ）
    
    Returns:
        dict: 作成されたロール割り当て
    
    Authorization:
        全体管理者のみ（Phase 2で実装）
    
    Business Logic:
        1. ユーザーの存在確認
        2. 重複チェック（同じservice_id + role_nameの組み合わせ）
        3. RoleAssignmentオブジェクト作成
        4. Cosmos DBに保存
        5. 監査ログ記録（assigned_by に現在のユーザーID）
    
    Performance:
        - 応答時間: < 300ms (P95)
    
    Error Codes:
        - 404: ユーザーが存在しない
        - 409: 同じロールが既に割り当て済み
        - 403: テナント分離違反、または権限不足
        - 400: サービスIDまたはロール名が不正
    """
    # テナント分離チェック（簡易実装）
    if current_user["tenant_id"] != data.tenant_id:
        logger.warning(
            f"Cross-tenant role assignment attempt: user_tenant={current_user['tenant_id']}, target_tenant={data.tenant_id}"
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "ROLE_006_TENANT_ISOLATION_VIOLATION",
                "message": "Cannot assign role to user in different tenant",
            },
        )

    # TODO: Phase 2で全体管理者チェックを追加（require_roleデコレータ）

    role_assignment = await role_service.assign_role(
        user_id, data, assigned_by=current_user["user_id"]
    )
    
    # 監査ログ記録
    logger.info(
        "Role assigned",
        extra={
            "action": "role.assign",
            "user_id": user_id,
            "tenant_id": data.tenant_id,
            "service_id": data.service_id,
            "role_name": data.role_name,
            "assigned_by": current_user["user_id"],
        },
    )
    
    return role_assignment.model_dump(by_alias=True)


@router.delete("/users/{user_id}/roles/{role_assignment_id}", status_code=204)
async def remove_role(
    user_id: str,
    role_assignment_id: str,
    tenant_id: str,
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user_from_request),
) -> None:
    """
    ユーザーからのロール削除
    
    Args:
        user_id: ユーザーID（パスパラメータ）
        role_assignment_id: ロール割り当てID（パスパラメータ）
        tenant_id: テナントID（クエリパラメータ）
    
    Returns:
        None: 204 No Content
    
    Authorization:
        全体管理者のみ（Phase 2で実装）
    
    Business Logic:
        1. RoleAssignmentの存在確認
        2. ユーザーIDの一致確認
        3. テナント分離チェック
        4. Cosmos DBから削除
        5. 監査ログ記録（deleted_by に現在のユーザーID）
    
    Performance:
        - 応答時間: < 200ms (P95)
    
    Error Codes:
        - 404: ロール割り当てが存在しない
        - 403: 権限不足
    """
    # テナント分離チェック（簡易実装）
    if current_user["tenant_id"] != tenant_id:
        logger.warning(
            f"Cross-tenant role removal attempt: user_tenant={current_user['tenant_id']}, target_tenant={tenant_id}"
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "ROLE_006_TENANT_ISOLATION_VIOLATION",
                "message": "Cannot remove role from user in different tenant",
            },
        )

    # TODO: Phase 2で全体管理者チェックを追加（require_roleデコレータ）

    await role_service.remove_role(user_id, role_assignment_id, tenant_id)
    
    # 監査ログ記録
    logger.info(
        "Role removed",
        extra={
            "action": "role.remove",
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role_assignment_id": role_assignment_id,
            "deleted_by": current_user["user_id"],
        },
    )
