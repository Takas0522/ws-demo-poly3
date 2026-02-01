"""依存注入の一元管理"""
from fastapi import Depends, Header, HTTPException, Request
from typing import Optional
import logging

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.models.user import User

logger = logging.getLogger(__name__)


def get_cosmos_container(request: Request):
    """
    Cosmos DBコンテナを取得
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        Cosmos DBコンテナクライアント
    
    Raises:
        RuntimeError: Cosmos DBが初期化されていない場合
    """
    if not hasattr(request.app.state, "cosmos_container"):
        raise RuntimeError("Cosmos DB not initialized")
    return request.app.state.cosmos_container


def get_user_repository(
    container=Depends(get_cosmos_container),
) -> UserRepository:
    """
    UserRepositoryの依存注入
    
    Args:
        container: Cosmos DBコンテナ
    
    Returns:
        UserRepositoryインスタンス
    """
    return UserRepository(container)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """
    AuthServiceの依存注入
    
    Args:
        user_repository: UserRepositoryインスタンス
    
    Returns:
        AuthServiceインスタンス
    """
    return AuthService(user_repository)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserService:
    """
    UserServiceの依存注入
    
    Args:
        user_repository: UserRepositoryインスタンス
        auth_service: AuthServiceインスタンス
    
    Returns:
        UserServiceインスタンス
    """
    return UserService(user_repository, auth_service)


async def get_current_user_from_token(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    """
    トークンから現在のユーザーを取得
    
    Args:
        authorization: Authorizationヘッダー
        auth_service: AuthServiceインスタンス
        user_repository: UserRepositoryインスタンス
    
    Returns:
        認証済みユーザーオブジェクト
    
    Raises:
        HTTPException: トークンが無効、またはユーザーが見つからない場合
    
    Note:
        共通ライブラリのMiddlewareは全エンドポイントに適用されるため、
        ここでは個別にトークン検証を行う
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    # "Bearer " プレフィックスを削除
    BEARER_PREFIX = "Bearer "
    token = authorization[len(BEARER_PREFIX):]
    
    # トークン検証
    token_data = auth_service.verify_token(token)

    # ユーザー情報を取得
    user = await user_repository.get(token_data.user_id, token_data.tenant_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
