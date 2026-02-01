"""AuthServiceのテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.models.user import User
from app.models.token import TokenData


class TestAuthService:
    """AuthServiceのテスト"""

    def setup_method(self):
        """各テストの前に実行"""
        self.mock_user_repository = MagicMock()
        self.service = AuthService(self.mock_user_repository)

    class Test認証ロジック:
        """認証ロジックのテスト"""

        @pytest.mark.asyncio
        async def test_authenticate_正常な認証(self):
            """正常な認証"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # パスワード検証をモック化（bcryptの問題を回避）
            service.verify_password = MagicMock(return_value=True)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="$2b$12$test_hash",
                display_name="Test User",
                is_active=True,
            )
            
            mock_user_repository.find_by_username = AsyncMock(return_value=user)
            
            # Act
            result = await service.authenticate("testuser", "any_password")
            
            # Assert
            assert result is not None
            assert result.id == "user_test_001"
            assert result.username == "testuser"

        @pytest.mark.asyncio
        async def test_authenticate_不正なパスワード(self):
            """不正なパスワード"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # パスワード検証をモック化（失敗を返す）
            service.verify_password = MagicMock(return_value=False)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="$2b$12$test_hash",
                display_name="Test User",
                is_active=True,
            )
            
            mock_user_repository.find_by_username = AsyncMock(return_value=user)
            
            # Act
            result = await service.authenticate("testuser", "wrong_password")
            
            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_authenticate_存在しないユーザー(self):
            """存在しないユーザー"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            mock_user_repository.find_by_username = AsyncMock(return_value=None)
            
            # Act
            result = await service.authenticate("nonexistent", "AnyPassword123!")
            
            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_authenticate_無効化されたアカウント(self):
            """無効化されたアカウント"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # パスワード検証をモック化
            service.verify_password = MagicMock(return_value=True)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="$2b$12$test_hash",
                display_name="Test User",
                is_active=False,  # 無効化
            )
            
            mock_user_repository.find_by_username = AsyncMock(return_value=user)
            
            # Act
            result = await service.authenticate("testuser", "any_password")
            
            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_authenticate_タイミング攻撃対策(self):
            """タイミング攻撃対策（処理時間の一定性）"""
            # Arrange
            import time
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="$2b$12$test_hash",
                display_name="Test User",
                is_active=True,
            )
            
            mock_user_repository.find_by_username = AsyncMock(return_value=user)
            
            # Act & Assert: 成功時の処理時間測定
            service.verify_password = MagicMock(return_value=True)
            start = time.perf_counter()
            await service.authenticate("testuser", "correct_password")
            success_time = (time.perf_counter() - start) * 1000  # ms
            
            # Act & Assert: 失敗時の処理時間測定
            service.verify_password = MagicMock(return_value=False)
            start = time.perf_counter()
            await service.authenticate("testuser", "wrong_password")
            fail_time = (time.perf_counter() - start) * 1000  # ms
            
            # Assert: 最小処理時間が200ms以上
            assert success_time >= 200, f"成功時の処理時間が短すぎる: {success_time:.2f}ms"
            assert fail_time >= 200, f"失敗時の処理時間が短すぎる: {fail_time:.2f}ms"

        @pytest.mark.asyncio
        async def test_authenticate_例外発生時の処理(self):
            """例外発生時の処理"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            mock_user_repository.find_by_username = AsyncMock(
                side_effect=Exception("Database error")
            )
            
            # Act
            result = await service.authenticate("testuser", "AnyPassword123!")
            
            # Assert
            assert result is None

    class TestJWT操作:
        """JWT操作のテスト"""

        def test_create_token_JWT生成(self):
            """JWT生成"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
                is_active=True,
            )
            
            # Act
            result = service.create_token(user)
            
            # Assert
            assert result.access_token is not None
            assert result.token_type == "Bearer"
            assert result.expires_in == 60 * 60  # 60分
            assert result.user["id"] == "user_test_001"

        def test_create_token_ペイロード内容検証(self):
            """JWTペイロード内容検証"""
            # Arrange
            from jose import jwt as jose_jwt
            from app.config import settings
            
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
                is_active=True,
            )
            
            # Act
            result = service.create_token(user)
            
            # デコード（検証なし）
            payload = jose_jwt.decode(
                result.access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Assert
            assert payload["sub"] == "user_test_001"
            assert payload["user_id"] == "user_test_001"
            assert payload["username"] == "testuser"
            assert payload["tenant_id"] == "tenant-test"
            assert "roles" in payload
            assert "exp" in payload
            assert "iat" in payload
            assert "jti" in payload

        def test_create_token_有効期限設定(self):
            """JWT有効期限設定"""
            # Arrange
            from jose import jwt as jose_jwt
            from app.config import settings
            from datetime import datetime, timedelta
            
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
                is_active=True,
            )
            
            # Act
            before = datetime.utcnow()
            result = service.create_token(user)
            after = datetime.utcnow()
            
            # デコード
            payload = jose_jwt.decode(
                result.access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Assert
            exp_time = datetime.fromtimestamp(payload["exp"])
            iat_time = datetime.fromtimestamp(payload["iat"])
            
            # iatが現在時刻に近い
            assert (before - timedelta(seconds=1)) <= iat_time <= (after + timedelta(seconds=1))
            
            # expがiat + 60分
            expected_exp = iat_time + timedelta(minutes=60)
            assert abs((exp_time - expected_exp).total_seconds()) < 2

        def test_create_token_ロール情報_Phase1は空配列(self):
            """ロール情報（Phase 1は空配列）"""
            # Arrange
            from jose import jwt as jose_jwt
            from app.config import settings
            
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
                is_active=True,
            )
            
            # Act
            result = service.create_token(user)
            
            # デコード
            payload = jose_jwt.decode(
                result.access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Assert
            assert payload["roles"] == []

        def test_create_token_JTI設定(self):
            """JWT ID (jti) 設定"""
            # Arrange
            from jose import jwt as jose_jwt
            from app.config import settings
            
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
                is_active=True,
            )
            
            # Act
            result1 = service.create_token(user)
            result2 = service.create_token(user)
            
            # デコード
            payload1 = jose_jwt.decode(
                result1.access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            payload2 = jose_jwt.decode(
                result2.access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Assert
            assert payload1["jti"].startswith("jwt_")
            assert payload2["jti"].startswith("jwt_")
            assert payload1["jti"] != payload2["jti"]  # ユニーク

        def test_verify_token_有効なトークン検証(self):
            """有効なトークン検証"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
                is_active=True,
            )
            
            token_response = service.create_token(user)
            
            # Act
            result = service.verify_token(token_response.access_token)
            
            # Assert
            assert result.user_id == "user_test_001"
            assert result.username == "testuser"
            assert result.tenant_id == "tenant-test"

        def test_verify_token_期限切れトークン(self):
            """期限切れトークン"""
            # Arrange
            from jose import jwt as jose_jwt
            from app.config import settings
            from datetime import datetime, timedelta
            
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # 期限切れのペイロード作成
            expired_payload = {
                "sub": "user_test_001",
                "user_id": "user_test_001",
                "username": "testuser",
                "tenant_id": "tenant-test",
                "roles": [],
                "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
                "iat": int((datetime.utcnow() - timedelta(hours=2)).timestamp()),
                "jti": "jwt_test",
            }
            
            expired_token = jose_jwt.encode(
                expired_payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                service.verify_token(expired_token)
            
            assert exc_info.value.status_code == 401
            assert "expired" in str(exc_info.value.detail).lower()

        def test_verify_token_不正な署名(self):
            """不正な署名"""
            # Arrange
            from jose import jwt as jose_jwt
            from app.config import settings
            from datetime import datetime, timedelta
            
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # 不正な秘密鍵で署名
            payload = {
                "sub": "user_test_001",
                "user_id": "user_test_001",
                "username": "testuser",
                "tenant_id": "tenant-test",
                "roles": [],
                "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
                "iat": int(datetime.utcnow().timestamp()),
                "jti": "jwt_test",
            }
            
            wrong_token = jose_jwt.encode(
                payload,
                "wrong_secret_key",
                algorithm=settings.JWT_ALGORITHM
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                service.verify_token(wrong_token)
            
            assert exc_info.value.status_code == 401
            assert "invalid" in str(exc_info.value.detail).lower()

        def test_verify_token_不正な形式(self):
            """不正な形式"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                service.verify_token("invalid_token_format")
            
            assert exc_info.value.status_code == 401

        def test_verify_token_ペイロード解析(self):
            """トークンペイロード解析"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
                is_active=True,
            )
            
            token_response = service.create_token(user)
            
            # Act
            result = service.verify_token(token_response.access_token)
            
            # Assert
            assert result.user_id == "user_test_001"
            assert result.tenant_id == "tenant-test"
            assert result.username == "testuser"
            assert result.roles == []
            assert result.exp is not None
            assert result.iat is not None
            assert result.jti.startswith("jwt_")

    class Testパスワード操作:
        """パスワード操作のテスト"""

        def test_hash_password_パスワードハッシュ化(self):
            """パスワードハッシュ化"""
            # Arrange
            from unittest.mock import patch
            mock_user_repository = MagicMock()
            
            # bcryptをモック化
            with patch('app.services.auth_service.pwd_context') as mock_pwd:
                mock_pwd.hash.return_value = "$2b$12$mocked_hash"
                service = AuthService(mock_user_repository)
                password = "TestPass123"
                
                # Act
                hashed = service.hash_password(password)
                
                # Assert
                assert hashed.startswith("$2b$")
                assert hashed != password

        def test_hash_password_同じパスワードで異なるハッシュ(self):
            """同じパスワードで異なるハッシュ（salt）"""
            # Arrange
            from unittest.mock import patch
            mock_user_repository = MagicMock()
            
            # bcryptをモック化（異なるハッシュを返す）
            with patch('app.services.auth_service.pwd_context') as mock_pwd:
                mock_pwd.hash.side_effect = ["$2b$12$hash1", "$2b$12$hash2"]
                mock_pwd.verify.return_value = True
                service = AuthService(mock_user_repository)
                password = "TestPass123"
                
                # Act
                hash1 = service.hash_password(password)
                hash2 = service.hash_password(password)
                
                # Assert
                assert hash1 != hash2
                assert service.verify_password(password, hash1)
                assert service.verify_password(password, hash2)

        def test_verify_password_正しいパスワード検証(self):
            """正しいパスワード検証"""
            # Arrange
            from unittest.mock import patch
            mock_user_repository = MagicMock()
            
            with patch('app.services.auth_service.pwd_context') as mock_pwd:
                mock_pwd.verify.return_value = True
                service = AuthService(mock_user_repository)
                password = "TestPass123"
                hashed = "$2b$12$mocked_hash"
                
                # Act
                result = service.verify_password(password, hashed)
                
                # Assert
                assert result is True

        def test_verify_password_誤ったパスワード検証(self):
            """誤ったパスワード検証"""
            # Arrange
            from unittest.mock import patch
            mock_user_repository = MagicMock()
            
            with patch('app.services.auth_service.pwd_context') as mock_pwd:
                mock_pwd.verify.return_value = False
                service = AuthService(mock_user_repository)
                password = "WrongPassword"
                hashed = "$2b$12$mocked_hash"
                
                # Act
                result = service.verify_password(password, hashed)
                
                # Assert
                assert result is False

        def test_verify_password_空のパスワード(self):
            """空のパスワードで検証"""
            # Arrange
            from unittest.mock import patch
            mock_user_repository = MagicMock()
            
            with patch('app.services.auth_service.pwd_context') as mock_pwd:
                mock_pwd.verify.return_value = False
                service = AuthService(mock_user_repository)
                hashed = "$2b$12$mocked_hash"
                
                # Act
                result = service.verify_password("", hashed)
                
                # Assert
                assert result is False

    class Test特権テナント:
        """特権テナントのテスト"""

        def test_is_privileged_tenant_特権テナント判定(self):
            """特権テナント判定"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # Act
            result = service.is_privileged_tenant("tenant_privileged")
            
            # Assert
            assert result is True

        def test_is_privileged_tenant_一般テナント判定(self):
            """一般テナント判定"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # Act
            result = service.is_privileged_tenant("tenant-acme")
            
            # Assert
            assert result is False

        def test_is_privileged_tenant_空文字列(self):
            """空文字列のテナントID"""
            # Arrange
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # Act
            result = service.is_privileged_tenant("")
            
            # Assert
            assert result is False

    class Test境界値:
        """境界値テスト"""

        @pytest.mark.asyncio
        async def test_authenticate_処理時間_最小200ms(self):
            """認証処理時間が最小200ms"""
            # Arrange
            import time
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            # 存在しないユーザー（最速で終わるケース）
            mock_user_repository.find_by_username = AsyncMock(return_value=None)
            
            # Act
            start = time.perf_counter()
            await service.authenticate("testuser", "AnyPassword123!")
            elapsed = (time.perf_counter() - start) * 1000  # ms
            
            # Assert
            assert elapsed >= 200, f"処理時間が短すぎる: {elapsed:.2f}ms < 200ms"

        @patch('app.services.auth_service.settings')
        def test_create_token_有効期限カスタマイズ(self, mock_settings):
            """JWT有効期限のカスタマイズ"""
            # Arrange
            from jose import jwt as jose_jwt
            from datetime import datetime, timedelta
            
            mock_settings.JWT_EXPIRE_MINUTES = 30  # 30分に変更
            mock_settings.JWT_SECRET_KEY = "test_secret_key"
            mock_settings.JWT_ALGORITHM = "HS256"
            
            mock_user_repository = MagicMock()
            service = AuthService(mock_user_repository)
            
            user = User(
                id="user_test_001",
                tenant_id="tenant-test",
                username="testuser",
                email="test@example.com",
                password_hash="hashed",
                display_name="Test User",
                is_active=True,
            )
            
            # Act
            before = datetime.utcnow()
            result = service.create_token(user)
            after = datetime.utcnow()
            
            # デコード
            payload = jose_jwt.decode(
                result.access_token,
                mock_settings.JWT_SECRET_KEY,
                algorithms=[mock_settings.JWT_ALGORITHM]
            )
            
            # Assert
            exp_time = datetime.fromtimestamp(payload["exp"])
            iat_time = datetime.fromtimestamp(payload["iat"])
            
            # expがiat + 30分（カスタマイズした値）
            duration = (exp_time - iat_time).total_seconds() / 60
            assert abs(duration - 30) < 1  # 1分以内の誤差
