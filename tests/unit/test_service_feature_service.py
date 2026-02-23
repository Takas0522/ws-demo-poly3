"""
Unit tests for ServiceFeatureService
TC-U-01 ~ TC-U-08
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.services.service_feature_service import ServiceFeatureService
from app.models.service_feature import ServiceFeature, TenantServiceFeature
from app.utils.auth import JWTPayload, Role


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repository):
    return ServiceFeatureService(repository=mock_repository)


@pytest.fixture
def sample_features():
    """3 件の ServiceFeature サンプル"""
    now = datetime.now(timezone.utc)
    return [
        ServiceFeature(
            id="feature-svc1-001",
            type="service_feature",
            service_id="svc-001",
            feature_key="chat",
            feature_name="チャット機能",
            description="チャット",
            default_enabled=True,
            created_at=now,
            partitionKey="svc-001",
        ),
        ServiceFeature(
            id="feature-svc1-002",
            type="service_feature",
            service_id="svc-001",
            feature_key="file_upload",
            feature_name="ファイルアップロード",
            description="ファイルアップロード機能",
            default_enabled=False,
            created_at=now,
            partitionKey="svc-001",
        ),
        ServiceFeature(
            id="feature-svc1-003",
            type="service_feature",
            service_id="svc-001",
            feature_key="analytics",
            feature_name="分析ダッシュボード",
            description="分析",
            default_enabled=True,
            created_at=now,
            partitionKey="svc-001",
        ),
    ]


@pytest.fixture
def admin_user():
    return JWTPayload(
        user_id="user-001",
        tenant_id="tenant-001",
        roles=[
            Role(service_id="svc-001", service_name="Service 1",
                 role_code="admin", role_name="Admin"),
        ],
    )


@pytest.fixture
def viewer_user():
    """admin / global_admin ロールを持たないユーザー"""
    return JWTPayload(
        user_id="user-002",
        tenant_id="tenant-001",
        roles=[
            Role(service_id="svc-001", service_name="Service 1",
                 role_code="viewer", role_name="Viewer"),
        ],
    )


# ---------------------------------------------------------------------------
# TC-U-01: get_service_features — サービス存在、3 件返却
# ---------------------------------------------------------------------------
class TestGetServiceFeatures:

    async def test_returns_features_when_service_exists(
        self, service, mock_repository, sample_features
    ):
        """TC-U-01: サービスが存在する場合、features を返す"""
        mock_repository.service_exists.return_value = True
        mock_repository.get_features_by_service_id.return_value = sample_features

        result = await service.get_service_features("svc-001")

        assert result.service_id == "svc-001"
        assert len(result.features) == 3
        assert result.features[0].feature_key == "chat"
        assert result.features[1].default_enabled is False
        mock_repository.service_exists.assert_awaited_once_with("svc-001")
        mock_repository.get_features_by_service_id.assert_awaited_once_with("svc-001")

    # -------------------------------------------------------------------
    # TC-U-02: get_service_features — サービス不存在で 404
    # -------------------------------------------------------------------
    async def test_raises_404_when_service_not_found(
        self, service, mock_repository
    ):
        """TC-U-02: サービスが存在しない場合 404"""
        mock_repository.service_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.get_service_features("non-existent")

        assert exc_info.value.status_code == 404
        assert "Service not found" in exc_info.value.detail


# ---------------------------------------------------------------------------
# TC-U-03 ~ TC-U-05: get_tenant_service_features
# ---------------------------------------------------------------------------
class TestGetTenantServiceFeatures:

    async def test_merges_tenant_settings_with_defaults(
        self, service, mock_repository, sample_features, admin_user
    ):
        """TC-U-03: テナント設定ありのマージ確認（is_default 混在）"""
        now = datetime.now(timezone.utc)
        # feature-svc1-001 のみカスタム設定あり（is_enabled=False に上書き）
        tenant_settings = [
            TenantServiceFeature(
                id="tenant-001_feature-svc1-001",
                type="tenant_service_feature",
                tenant_id="tenant-001",
                service_id="svc-001",
                feature_id="feature-svc1-001",
                feature_key="chat",
                is_enabled=False,
                updated_at=now,
                updated_by="user-001",
                partitionKey="tenant-001",
            ),
        ]

        mock_repository.get_tenant_service.return_value = {"id": "ts-001"}
        mock_repository.get_features_by_service_id.return_value = sample_features
        mock_repository.get_tenant_feature_settings.return_value = tenant_settings

        result = await service.get_tenant_service_features(
            tenant_id="tenant-001",
            service_id="svc-001",
            current_user=admin_user,
        )

        assert result.tenant_id == "tenant-001"
        assert result.service_id == "svc-001"
        assert len(result.features) == 3

        # feature-svc1-001: カスタム設定
        f1 = result.features[0]
        assert f1.feature_id == "feature-svc1-001"
        assert f1.is_enabled is False  # テナント設定で上書き
        assert f1.is_default is False

        # feature-svc1-002: デフォルト (default_enabled=False)
        f2 = result.features[1]
        assert f2.feature_id == "feature-svc1-002"
        assert f2.is_enabled is False
        assert f2.is_default is True

        # feature-svc1-003: デフォルト (default_enabled=True)
        f3 = result.features[2]
        assert f3.feature_id == "feature-svc1-003"
        assert f3.is_enabled is True
        assert f3.is_default is True

    async def test_all_defaults_when_no_tenant_settings(
        self, service, mock_repository, sample_features, admin_user
    ):
        """TC-U-04: テナント設定なし、全デフォルト"""
        mock_repository.get_tenant_service.return_value = {"id": "ts-001"}
        mock_repository.get_features_by_service_id.return_value = sample_features
        mock_repository.get_tenant_feature_settings.return_value = []

        result = await service.get_tenant_service_features(
            tenant_id="tenant-001",
            service_id="svc-001",
            current_user=admin_user,
        )

        for feat in result.features:
            assert feat.is_default is True
            assert feat.updated_at is None
            assert feat.updated_by is None

        # default_enabled の値がそのまま反映
        assert result.features[0].is_enabled is True   # chat
        assert result.features[1].is_enabled is False   # file_upload
        assert result.features[2].is_enabled is True    # analytics

    async def test_raises_403_when_service_not_assigned(
        self, service, mock_repository, admin_user
    ):
        """TC-U-05: サービス未割り当て（403）"""
        mock_repository.get_tenant_service.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_tenant_service_features(
                tenant_id="tenant-001",
                service_id="svc-999",
                current_user=admin_user,
            )

        assert exc_info.value.status_code == 403
        assert "not assigned" in exc_info.value.detail


# ---------------------------------------------------------------------------
# TC-U-06 ~ TC-U-08: update_tenant_service_feature
# ---------------------------------------------------------------------------
class TestUpdateTenantServiceFeature:

    async def test_upsert_success(
        self, service, mock_repository, sample_features, admin_user
    ):
        """TC-U-06: 新規 upsert 正常系"""
        feature = sample_features[0]  # feature-svc1-001

        mock_repository.get_tenant_service.return_value = {"id": "ts-001"}
        mock_repository.get_feature_by_id.return_value = feature
        mock_repository.upsert_tenant_feature.return_value = None

        result = await service.update_tenant_service_feature(
            tenant_id="tenant-001",
            service_id="svc-001",
            feature_id="feature-svc1-001",
            is_enabled=False,
            current_user=admin_user,
        )

        assert result.feature_id == "feature-svc1-001"
        assert result.is_enabled is False
        assert result.is_default is False
        assert result.updated_by == "user-001"
        assert result.updated_at is not None
        mock_repository.upsert_tenant_feature.assert_awaited_once()

    async def test_raises_404_when_feature_not_found(
        self, service, mock_repository, admin_user
    ):
        """TC-U-07: 存在しない feature_id（404）"""
        mock_repository.get_tenant_service.return_value = {"id": "ts-001"}
        mock_repository.get_feature_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.update_tenant_service_feature(
                tenant_id="tenant-001",
                service_id="svc-001",
                feature_id="non-existent-feature",
                is_enabled=True,
                current_user=admin_user,
            )

        assert exc_info.value.status_code == 404
        assert "Feature not found" in exc_info.value.detail

    async def test_raises_403_when_insufficient_role(
        self, service, mock_repository, viewer_user
    ):
        """TC-U-08: ロール不足（403）"""
        with pytest.raises(HTTPException) as exc_info:
            await service.update_tenant_service_feature(
                tenant_id="tenant-001",
                service_id="svc-001",
                feature_id="feature-svc1-001",
                is_enabled=True,
                current_user=viewer_user,
            )

        assert exc_info.value.status_code == 403
        # has_role 失敗時はリポジトリを呼ばない
        mock_repository.get_tenant_service.assert_not_awaited()
