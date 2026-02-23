"""
Unit tests for ServiceFeatureRepository
TC-U-09 ~ TC-U-10
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.repositories.service_feature_repository import ServiceFeatureRepository
from app.models.service_feature import ServiceFeature, TenantServiceFeature


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repository():
    """モック済み Cosmos DB コンテナを持つリポジトリ"""
    repo = ServiceFeatureRepository()
    repo.services_container = AsyncMock()
    repo.tenant_services_container = AsyncMock()
    return repo


# ---------------------------------------------------------------------------
# TC-U-09: get_features_by_service_id — 正しいクエリと partition_key
# ---------------------------------------------------------------------------
class TestGetFeaturesByServiceId:

    async def test_queries_with_correct_parameters(self, repository):
        """TC-U-09: 正しいクエリとパーティションキーで query_items を呼ぶ"""
        now = datetime.now(timezone.utc)
        raw_items = [
            {
                "id": "feature-svc1-001",
                "type": "service_feature",
                "service_id": "svc-001",
                "feature_key": "chat",
                "feature_name": "チャット機能",
                "description": "チャット",
                "default_enabled": True,
                "created_at": now.isoformat(),
                "partitionKey": "svc-001",
            },
            {
                "id": "feature-svc1-002",
                "type": "service_feature",
                "service_id": "svc-001",
                "feature_key": "file_upload",
                "feature_name": "ファイルアップロード",
                "description": "",
                "default_enabled": False,
                "created_at": now.isoformat(),
                "partitionKey": "svc-001",
            },
        ]

        # Cosmos SDK の query_items は async iterator を返す
        async def mock_query_items(**kwargs):
            for item in raw_items:
                yield item

        repository.services_container.query_items = MagicMock(
            side_effect=mock_query_items
        )

        result = await repository.get_features_by_service_id("svc-001")

        # 結果の検証
        assert len(result) == 2
        assert all(isinstance(f, ServiceFeature) for f in result)
        assert result[0].feature_key == "chat"
        assert result[1].feature_key == "file_upload"

        # query_items の呼び出し引数を検証
        call_kwargs = repository.services_container.query_items.call_args
        assert "partition_key" in call_kwargs.kwargs
        assert call_kwargs.kwargs["partition_key"] == "svc-001"
        assert "@serviceId" in call_kwargs.kwargs["query"]
        assert call_kwargs.kwargs["parameters"] == [
            {"name": "@serviceId", "value": "svc-001"}
        ]


# ---------------------------------------------------------------------------
# TC-U-10: upsert_tenant_feature — tenantId フィールド追加の確認
# ---------------------------------------------------------------------------
class TestUpsertTenantFeature:

    async def test_adds_tenantId_field_and_calls_upsert(self, repository):
        """TC-U-10: upsert 時に tenantId フィールドが body に追加される"""
        now = datetime.now(timezone.utc)
        tenant_feature = TenantServiceFeature(
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
        )

        repository.tenant_services_container.upsert_item = AsyncMock()

        result = await repository.upsert_tenant_feature(tenant_feature)

        # 戻り値が同じオブジェクトであること
        assert result is tenant_feature

        # upsert_item が呼ばれたこと
        repository.tenant_services_container.upsert_item.assert_awaited_once()

        # body の内容を検証
        call_kwargs = repository.tenant_services_container.upsert_item.call_args
        body = call_kwargs.kwargs["body"]

        # tenantId が追加されていること
        assert "tenantId" in body
        assert body["tenantId"] == "tenant-001"

        # 基本フィールドも含まれていること
        assert body["id"] == "tenant-001_feature-svc1-001"
        assert body["tenant_id"] == "tenant-001"
        assert body["is_enabled"] is False
