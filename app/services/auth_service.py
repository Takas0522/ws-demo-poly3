"""認証サービス"""
from typing import Optional
from datetime import datetime, timedelta
import uuid
import logging
import asyncio
from jose import jwt
from passlib.context import CryptContext

from app.models.user import User
from app.models.token import TokenData, TokenResponse
from app.repositories.user_repository import UserRepository
from app.config import settings

logger = logging.getLogger(__name__)

# パスワードハッシュ化設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 最小認証処理時間（タイミング攻撃対策）: 200ms
MIN_AUTH_DURATION_MS = 200


class AuthService:
    """認証サービス"""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.logger = logger

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """パスワード検証"""
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """パスワードハッシュ化"""
        return pwd_context.hash(password)

    async def authenticate(
        self, username: str, password: str
    ) -> Optional[User]:
        """
        ユーザー認証（タイミング攻撃対策あり）
        
        Args:
            username: 認証するユーザー名
            password: 平文パスワード
        
        Returns:
            認証成功時はUserオブジェクト、失敗時はNone
        
        Note:
            タイミング攻撃対策のため、ユーザーの存在に関わらず
            最小処理時間を確保します。ログにはユーザー名を記録せず、
            統一されたメッセージのみを出力します。
        """
        start_time = datetime.utcnow()
        
        try:
            # 1. ユーザー検索（全テナント対象）
            user = await self.user_repository.find_by_username(username)
            
            # 2. パスワード検証（タイミング攻撃対策）
            # ユーザーが存在しない場合もダミーハッシュで時間を消費
            is_valid = False
            if user:
                is_valid = self.verify_password(password, user.password_hash)
            else:
                # ダミーハッシュで同じ処理時間を確保
                self.verify_password(password, self.hash_password("dummy_password"))
            
            # 3. 認証結果判定
            if not user or not is_valid or not user.is_active:
                # セキュリティのため、詳細な失敗理由は記録しない
                self.logger.warning(
                    "Failed authentication attempt",
                    extra={"username_length": len(username)}
                )
                # タイミング攻撃対策: 最小処理時間を確保
                await self._ensure_min_duration(start_time)
                return None
            
            self.logger.info(
                "Successful authentication",
                extra={"user_id": user.id, "tenant_id": user.tenant_id}
            )
            
            # タイミング攻撃対策: 最小処理時間を確保
            await self._ensure_min_duration(start_time)
            return user

        except Exception as e:
            self.logger.error(
                "Authentication error occurred",
                extra={"error_type": type(e).__name__}
            )
            # タイミング攻撃対策: 最小処理時間を確保
            await self._ensure_min_duration(start_time)
            return None
    
    async def _ensure_min_duration(self, start_time: datetime) -> None:
        """
        最小処理時間を確保（タイミング攻撃対策）
        
        Args:
            start_time: 処理開始時刻
        """
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        remaining_ms = max(0, MIN_AUTH_DURATION_MS - elapsed_ms)
        if remaining_ms > 0:
            await asyncio.sleep(remaining_ms / 1000)

    def is_privileged_tenant(self, tenant_id: str) -> bool:
        """
        特権テナント判定
        
        Args:
            tenant_id: テナントID
        
        Returns:
            特権テナントの場合True
        """
        return tenant_id in settings.PRIVILEGED_TENANT_IDS
    
    async def create_token(self, user: User) -> TokenResponse:
        """
        JWT生成（ロール情報含む - タスク04で更新）
        
        Args:
            user: ユーザーオブジェクト
        
        Returns:
            TokenResponse: トークンレスポンス
        
        Note:
            タスク04でロール情報を含めるように更新。
            ユーザーのロール情報を取得し、JWTペイロードに含める。
        
        Performance:
            - JWT生成（ロール情報含む）: < 100ms (P95)
            - ロール数制限: 最大20件
        """
        # トークンの有効期限
        expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        issued_at = datetime.utcnow()

        # 1. ユーザーのロール情報を取得（タスク04で追加）
        from app.repositories.role_repository import RoleRepository
        
        role_repository = RoleRepository(self.user_repository.container)
        role_assignments = await role_repository.get_by_user_id(user.id, user.tenant_id)
        
        # 2. ロール情報を整形
        roles = [
            {"service_id": ra.service_id, "role_name": ra.role_name}
            for ra in role_assignments
        ]
        
        # 最大ロール数の制限（パフォーマンス保証）
        if len(roles) > 20:
            self.logger.warning(
                f"User has too many roles: user_id={user.id}, count={len(roles)}"
            )
            roles = roles[:20]  # 上位20件のみ

        # 3. JWTペイロード作成
        payload = {
            "sub": user.id,  # ユーザーID
            "user_id": user.id,
            "username": user.username,
            "tenant_id": user.tenant_id,
            "roles": roles,  # ロール情報を含める（タスク04で更新）
            "exp": int(expire.timestamp()),
            "iat": int(issued_at.timestamp()),
            "jti": f"jwt_{uuid.uuid4()}",
        }

        # JWT生成
        token = jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        # レスポンス作成
        return TokenResponse(
            access_token=token,
            token_type="Bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "tenant_id": user.tenant_id,
                "is_active": user.is_active,
            },
        )

    def verify_token(self, token: str) -> TokenData:
        """
        JWT検証
        
        Args:
            token: JWTトークン
        
        Returns:
            TokenData: デコード済みトークンデータ
        
        Raises:
            HTTPException: トークンが無効な場合
        """
        from fastapi import HTTPException

        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )

            # TokenDataに変換
            token_data = TokenData(
                user_id=payload.get("user_id"),
                tenant_id=payload.get("tenant_id"),
                username=payload.get("username"),
                roles=payload.get("roles", []),
                exp=payload.get("exp"),
                iat=payload.get("iat"),
                jti=payload.get("jti"),
            )

            return token_data

        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError as e:
            self.logger.warning(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
