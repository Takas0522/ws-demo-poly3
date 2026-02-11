# 利用サービス設定サービス (Service Setting Service)

## 概要

本サービスは、テナントごとのサービス利用設定を管理するマイクロサービスです。
各テナントが利用できるサービスを割り当て、利用状況を管理します。

## 技術スタック

- **フレームワーク**: FastAPI
- **言語**: Python 3.11+
- **データベース**: Azure Cosmos DB (NoSQL API)
- **バリデーション**: Pydantic
- **認証**: JWT (JSON Web Token)

## ディレクトリ構造

```
src/service-setting-service/
├── app/
│   ├── main.py              # FastAPIアプリケーションエントリーポイント
│   ├── api/                 # APIエンドポイント
│   │   └── v1/
│   │       ├── services.py  # サービス管理エンドポイント
│   │       └── tenant_services.py # テナントサービス割り当て
│   ├── models/              # データモデル（Pydantic）
│   │   ├── service.py
│   │   └── tenant_service.py
│   ├── repositories/        # データアクセス層
│   │   ├── service_repository.py
│   │   └── tenant_service_repository.py
│   ├── services/            # ビジネスロジック層
│   │   ├── service_service.py
│   │   └── tenant_service_service.py
│   ├── core/                # コア機能
│   │   ├── config.py        # 設定管理
│   │   ├── database.py      # DB接続管理
│   │   └── dependencies.py  # 依存性注入
│   └── utils/               # ユーティリティ
│       ├── logger.py
│       └── exceptions.py
├── tests/                   # テストコード
│   ├── unit/
│   └── integration/
├── .env                     # 環境変数
├── requirements.txt         # Python依存関係
├── Dockerfile              # Dockerイメージ定義
└── README.md               # このファイル
```

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルを作成：

```bash
# Cosmos DB
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=your-cosmos-key
COSMOS_DATABASE_NAME=service_management

# Application
APP_NAME=Service Setting Service
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# Other Services
TENANT_SERVICE_URL=http://localhost:8002
```

### 3. データベースの初期化

```bash
python -m app.scripts.init_db
```

初期データ（モックサービス含む）を自動で登録します：

- ファイル管理サービス
- メッセージングサービス
- API利用サービス
- バックアップサービス

### 4. サービスの起動

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

API ドキュメント: http://localhost:8003/docs

## 開発

### 新しいサービスの追加

```python
# app/scripts/init_db.py
services = [
    {
        "id": "service-uuid",
        "code": "new_service",
        "name": "新規サービス",
        "description": "新しいサービスの説明",
        "available_roles": [
            {"code": "admin", "name": "管理者"},
            {"code": "user", "name": "ユーザー"}
        ]
    }
]
```

### サービス割り当てロジック

```python
# app/services/tenant_service_service.py
class TenantServiceService:
    async def assign_service(
        self,
        tenant_id: str,
        service_id: str
    ) -> TenantService:
        # テナント存在チェック
        # サービス存在チェック
        # 重複チェック
        # 割り当て実行
        pass
```

### ロール情報の収集

各サービスから利用可能なロールを取得：

```python
# app/services/service_service.py
async def get_available_roles(self, service_id: str) -> List[Role]:
    """
    指定されたサービスで利用可能なロール一覧を取得
    """
    service = await self.service_repo.get_by_id(service_id)
    return service.available_roles
```

## テスト

### ユニットテスト

```bash
pytest tests/unit/
```

### 統合テスト

```bash
pytest tests/integration/
```

## API エンドポイント

### サービス管理

#### サービス一覧取得

```http
GET /api/v1/services
Authorization: Bearer {token}
```

**レスポンス**:

```json
{
  "items": [
    {
      "id": "service-uuid",
      "code": "file_management",
      "name": "ファイル管理サービス",
      "description": "ファイルのアップロード・管理機能を提供",
      "available_roles": [
        { "code": "admin", "name": "管理者" },
        { "code": "user", "name": "ユーザー" }
      ],
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### サービス詳細取得

```http
GET /api/v1/services/{service_id}
Authorization: Bearer {token}
```

#### サービス作成

```http
POST /api/v1/services
Authorization: Bearer {token}
Content-Type: application/json

{
  "code": "new_service",
  "name": "新規サービス",
  "description": "サービスの説明",
  "available_roles": [
    {"code": "admin", "name": "管理者"}
  ]
}
```

### テナントサービス割り当て

#### テナントのサービス一覧取得

```http
GET /api/v1/tenant-services?tenant_id={tenant_id}
Authorization: Bearer {token}
```

**レスポンス**:

```json
{
  "items": [
    {
      "id": "tenant-service-uuid",
      "tenant_id": "tenant-uuid",
      "service_id": "service-uuid",
      "service": {
        "name": "ファイル管理サービス",
        "code": "file_management"
      },
      "assigned_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### サービス割り当て

```http
POST /api/v1/tenant-services
Authorization: Bearer {token}
Content-Type: application/json

{
  "tenant_id": "tenant-uuid",
  "service_id": "service-uuid"
}
```

#### サービス割り当て解除

```http
DELETE /api/v1/tenant-services/{tenant_service_id}
Authorization: Bearer {token}
```

詳細は [API設計仕様書](./docs/api-specification.md) を参照してください。

## データモデル

### Service

```json
{
  "id": "service-uuid",
  "type": "service",
  "code": "file_management",
  "name": "ファイル管理サービス",
  "description": "ファイルのアップロード・管理機能を提供",
  "available_roles": [
    {
      "code": "admin",
      "name": "管理者",
      "description": "ファイルのアップロード・削除が可能"
    },
    {
      "code": "user",
      "name": "ユーザー",
      "description": "ファイルの閲覧・ダウンロードが可能"
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "partition_key": "service-uuid"
}
```

### TenantService

```json
{
  "id": "tenant-service-uuid",
  "type": "tenant_service",
  "tenant_id": "tenant-uuid",
  "service_id": "service-uuid",
  "assigned_at": "2024-01-15T10:00:00Z",
  "partition_key": "tenant-uuid"
}
```

詳細は [データ設計](../../docs/arch/data/data-model.md#23-サービス管理データモデル) を参照してください。

## モックサービス

以下のサービスは初期データとして登録されます：

### 1. ファイル管理サービス

- **コード**: `file_management`
- **ロール**: 管理者、ユーザー
- **機能**: ファイルのアップロード・管理

### 2. メッセージングサービス

- **コード**: `messaging`
- **ロール**: 管理者、ユーザー
- **機能**: メッセージの送信・閲覧

### 3. API利用サービス

- **コード**: `api_usage`
- **ロール**: 管理者、ユーザー
- **機能**: API設定・利用

### 4. バックアップサービス

- **コード**: `backup`
- **ロール**: 管理者、閲覧者
- **機能**: バックアップの実行・復元

## ビジネスルール

### サービス割り当て

1. **重複チェック**: 同じテナントに同じサービスを重複して割り当てできません
2. **テナント存在チェック**: 存在しないテナントにはサービスを割り当てできません
3. **全体管理者のみ**: サービス割り当ては「全体管理者」ロールのみ実行可能

### ロール管理

- テナントが利用できるサービスに応じて、そのサービスのロールのみが設定可能
- 利用できないサービスのロールは表示・設定されません

## トラブルシューティング

### Q: 初期データが登録されない

```bash
# 手動で初期化スクリプトを実行
python -m app.scripts.init_db

# データが登録されているか確認
# Azure Portal または Cosmos DB Emulator で確認
```

### Q: テナントサービスが取得できない

```bash
# テナント管理サービスと連携できているか確認
echo $TENANT_SERVICE_URL
curl http://localhost:8002/health
```

## 関連ドキュメント

- [コンポーネント設計](./docs/component-design.md)
- [API設計仕様書](./docs/api-specification.md)
- [API共通仕様](../../docs/arch/api/api-specification.md)
- [データ設計](../../docs/arch/data/data-model.md#23-サービス管理データモデル)
- [アーキテクチャ概要](../../docs/arch/overview.md)
- [IaC定義](./infra/container-app.bicep)

## ライセンス

MIT License
