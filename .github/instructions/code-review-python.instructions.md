---
applyTo: "src/auth-service/**/*.py,src/tenant-management-service/**/*.py,src/service-setting-service/**/*.py,src/shared/**/*.py,scripts/**/*.py"
excludeAgent: "coding-agent"
---

# Python / FastAPI コードレビューガイドライン

## レビューコメントの言語

- **レビューコメントはすべて日本語で記述すること**
- コード例やコマンドはそのままでよいが、指摘・提案・質問の説明文は必ず日本語で書く

## アーキテクチャレイヤーの遵守

各バックエンドサービスは以下のレイヤー構成に従う。レイヤーの責務違反を指摘する。

- `api/v1/` — ルートハンドラ（リクエスト受付、レスポンス返却のみ）
- `schemas/` — Pydantic リクエスト/レスポンス DTO
- `models/` — Cosmos DB ドキュメントに対応するドメインモデル
- `repositories/` — データアクセス層（Cosmos DB 操作のみ）
- `services/` — ビジネスロジック層
- `utils/` — 横断的ユーティリティ（JWT、依存性注入、テレメトリ）

ビジネスロジックが `api/` 層に漏れ出していないか、データベース操作が `services/` 層に直接実装されていないか確認する。違反があれば日本語で理由と改善案を指摘する。

## 命名規則

- ファイル名・モジュール名: `snake_case`（例: `user_repository.py`）
- クラス名: `PascalCase`（例: `UserRepository`, `TenantService`）
- 関数名・変数名: `snake_case`（例: `get_by_user_id`, `tenant_id`）
- 定数: `UPPER_CASE`

## Pydantic モデルのパターン

- `schemas/` のフィールドは `snake_case` で定義する
- `models/` のフィールドには Cosmos DB との互換性のため `camelCase` の `alias` を設定する
- `models/` には `populate_by_name = True` の `Config` を持たせる
- Create / Update / Response / ListResponse を分離する

```python
# schemas/ — 正しい例
class UserCreate(BaseModel):
    user_id: str = Field(..., description="ユーザーID")
    name: str = Field(..., min_length=1, max_length=100)

# models/ — 正しい例
class User(BaseModel):
    user_id: str = Field(..., alias="userId")
    partition_key: str = Field(..., alias="partitionKey")

    class Config:
        populate_by_name = True
```

- `Field(...)` で `description`、`min_length`、`max_length` 等のバリデーション制約が適切に設定されているか確認する

## リポジトリ層の規則

- Cosmos DB クエリにはパラメータ化クエリ（`@parameter`）を使用する（SQLインジェクション防止）
- `enable_cross_partition_query=True` が必要な場合のみ設定されているか確認する
- `model_dump(by_alias=True)` で Cosmos DB への書き込みが行われているか確認する

## API エンドポイントの規則

- 適切な `status_code` が設定されているか確認する（POST=201、DELETE=204 等）
- `response_model` が設定されているか確認する
- 日本語のdocstringが記述されているか確認する
- ページネーション対応エンドポイントでは `Query` パラメータに `ge`/`le` 制約があるか確認する

```python
# 正しい例
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(...):
    """ユーザー作成"""

# 避けるべき例
@router.post("")
async def create_user(...):
```

## 認証・認可

- 保護対象エンドポイントに `Depends(get_current_user)` または `Depends(require_role([...]))` が設定されているか確認する
- ヘルスチェック (`/health`) とログイン (`/api/v1/auth/login`) は認証不要であること
- ロールチェックのロール名が既知のロールコードと一致しているか確認する

## コードスタイル

- 型ヒントが関数シグネチャに記述されているか確認する
- `async def` が適切に使用されているか確認する
- コメント・docstringは日本語で記述されているか確認する（エラーメッセージの `detail` は英語）
- `from __future__ import annotations` の一貫した使用を確認する
- `datetime.utcnow()` によるタイムスタンプ生成が一貫しているか確認する

## 設定管理

- 環境固有の値が `Settings`（pydantic-settings）経由で管理されているか確認する
- ハードコードされた接続文字列やポート番号がないか確認する
- `@lru_cache()` パターンの `get_settings()` が維持されているか確認する

## テスト

- `@pytest.mark.integration` マーカーが使用されているか確認する
- `TestClient` または `httpx.AsyncClient` によるAPIテストのパターンが一貫しているか確認する
- テストクラスベースの構成に従っているか確認する

※ 本ファイルに記載されたすべての観点について、レビューコメントは日本語で記述すること。
