# 利用サービス設定サービス コンポーネント設計

## ドキュメント情報

- **バージョン**: 1.0.0
- **最終更新日**: 2024年
- **ステータス**: Draft

---

## 1. 概要

SaaSプラットフォームで利用可能なサービスの管理とテナントへの割り当てを担当するマイクロサービスです。

## 2. ディレクトリ構造

```
src/service-setting-service/
├── app/
│   ├── main.py                 # FastAPIアプリケーション
│   ├── config.py               # 設定管理
│   ├── models/                 # データモデル
│   │   └── service.py
│   ├── schemas/                # Pydanticスキーマ
│   │   └── service.py
│   ├── repositories/           # データアクセス層
│   │   └── service_repository.py
│   ├── services/               # ビジネスロジック
│   │   └── service_service.py
│   ├── api/                    # APIエンドポイント
│   │   └── v1/
│   │       └── services.py
│   └── utils/                  # ユーティリティ
│       └── dependencies.py
├── tests/
├── infra/                      # IaC定義
│   └── container-app.bicep
├── Dockerfile
└── requirements.txt
```

## 3. 主要機能

### 3.1 サービス管理

**サービス登録**

```python
class ServiceManagementService:
    async def register_service(self, data: ServiceCreate) -> Service:
        service = Service(
            id=generate_uuid(),
            service_name=data.service_name,
            display_name=data.display_name,
            description=data.description,
            api_url=data.api_url,
            is_active=True,
            created_at=datetime.utcnow()
        )

        await self.service_repo.create(service)
        return service
```

**サービス一覧取得**

```python
class ServiceManagementService:
    async def list_services(
        self,
        page: int = 1,
        per_page: int = 20,
        active_only: bool = False
    ) -> PaginatedResponse[Service]:
        return await self.service_repo.list_with_pagination(
            page, per_page, active_only=active_only
        )
```

### 3.2 テナント-サービス紐付け

**テナントへのサービス割り当て**

```python
class ServiceManagementService:
    async def assign_service_to_tenant(
        self,
        tenant_id: str,
        service_id: str
    ) -> TenantService:
        # サービス存在確認
        service = await self.service_repo.get_by_id(service_id)
        if not service:
            raise NotFoundError(f"Service {service_id} not found")

        # 重複チェック
        existing = await self.service_repo.get_tenant_service(
            tenant_id, service_id
        )
        if existing:
            raise ConflictError("Service already assigned to tenant")

        # 紐付け作成
        assignment = TenantService(
            id=generate_uuid(),
            tenant_id=tenant_id,
            service_id=service_id,
            is_active=True,
            assigned_at=datetime.utcnow()
        )

        await self.service_repo.create_assignment(assignment)
        return assignment
```

**テナントの利用サービス一覧**

```python
class ServiceManagementService:
    async def get_tenant_services(
        self,
        tenant_id: str
    ) -> List[Service]:
        return await self.service_repo.get_services_by_tenant(tenant_id)
```

### 3.3 ロール定義公開

```python
class ServiceManagementService:
    async def get_service_roles(self, service_id: str) -> List[RoleDefinition]:
        """サービスが定義するロール一覧を取得（認証サービスから収集される）"""
        return await self.service_repo.get_roles(service_id)
```

## 4. データモデル

```python
class Service(BaseModel):
    id: str
    service_name: str
    display_name: str
    description: Optional[str] = None
    api_url: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

class TenantServiceAssignment(BaseModel):
    id: str
    tenant_id: str
    service_id: str
    is_active: bool = True
    assigned_at: datetime
    revoked_at: Optional[datetime] = None

class RoleDefinition(BaseModel):
    id: str
    service_id: str
    role_code: str
    role_name: str
    description: str
```

データベース詳細は [データ設計](../../../docs/arch/data/data-model.md) を参照してください。

## 5. 環境変数

```bash
# Database
COSMOS_DB_ENDPOINT=https://xxx.documents.azure.com:443/
COSMOS_DB_KEY=xxx
COSMOS_DB_DATABASE=service_management

# Service
SERVICE_NAME=service-setting-service
PORT=8003
```

---

## 変更履歴

| バージョン | 日付 | 変更内容                                   | 作成者             |
| ---------- | ---- | ------------------------------------------ | ------------------ |
| 1.0.0      | 2024 | 初版作成（統合コンポーネント設計から分離） | Architecture Agent |
