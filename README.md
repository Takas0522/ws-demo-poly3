# 認証認可サービス

マルチテナント管理アプリケーションの認証認可サービスです。

## 概要

ユーザー認証とJWT管理を行うコアサービスです。

### 主要機能

- **認証API**
  - ログイン (POST /api/v1/auth/login)
  - JWT検証 (POST /api/v1/auth/verify)
  - ログアウト (POST /api/v1/auth/logout)
  - 現在のユーザー情報取得 (GET /api/v1/auth/me)

- **ユーザー管理API**
  - ユーザー一覧取得 (GET /api/v1/users)
  - ユーザー詳細取得 (GET /api/v1/users/{user_id})
  - ユーザー作成 (POST /api/v1/users)
  - ユーザー更新 (PUT /api/v1/users/{user_id})
  - ユーザー削除 (DELETE /api/v1/users/{user_id})

## 技術スタック

- **言語**: Python 3.11+
- **フレームワーク**: FastAPI 0.100+
- **データベース**: Azure Cosmos DB
- **認証**: JWT (python-jose)
- **パスワードハッシュ**: bcrypt (passlib)

## セットアップ

### 1. 環境変数設定

`.env.example` をコピーして `.env` ファイルを作成：

```bash
cp .env.example .env
```

必須の環境変数：
- `COSMOS_DB_CONNECTION_STRING`: Cosmos DB接続文字列
- `JWT_SECRET_KEY`: JWT署名用秘密鍵（64文字以上）

### 2. 依存パッケージインストール

```bash
# 本番用
pip install -r requirements.txt

# 開発用（テストツール含む）
pip install -r requirements-dev.txt
```

### 3. ローカル起動

```bash
# 開発モード（ホットリロード有効）
python -m app.main

# または uvicorn直接実行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

サービスが起動したら、以下のURLにアクセス可能：
- API ドキュメント: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- ヘルスチェック: http://localhost:8000/health

## API使用例

### ログイン

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@example.com",
    "password": "SecureP@ssw0rd123"
  }'
```

レスポンス：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_550e8400-...",
    "username": "admin@example.com",
    "email": "admin@example.com",
    "display_name": "管理者",
    "tenant_id": "tenant_123",
    "is_active": true
  }
}
```

### JWT検証

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### 現在のユーザー情報取得

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### ユーザー一覧取得

```bash
curl -X GET "http://localhost:8000/api/v1/users?tenant_id=tenant_123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### ユーザー作成

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser@example.com",
    "email": "newuser@example.com",
    "password": "SecureP@ssw0rd123",
    "displayName": "新規ユーザー",
    "tenantId": "tenant_123"
  }'
```

## テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=app --cov-report=html

# 特定のテストファイルのみ
pytest tests/test_api_auth.py

# マーカーで絞り込み
pytest -m "not slow"
```

## プロジェクト構造

```
src/auth-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPIアプリ
│   ├── config.py               # 設定
│   ├── api/                    # APIエンドポイント
│   │   ├── auth.py             # 認証API
│   │   └── users.py            # ユーザー管理API
│   ├── models/                 # データモデル
│   │   ├── user.py
│   │   └── token.py
│   ├── schemas/                # リクエスト/レスポンススキーマ
│   │   ├── auth.py
│   │   └── user.py
│   ├── services/               # ビジネスロジック
│   │   ├── auth_service.py
│   │   └── user_service.py
│   └── repositories/           # データアクセス層
│       └── user_repository.py
├── tests/                      # テストコード
├── .env.example               # 環境変数テンプレート
├── requirements.txt           # 本番依存パッケージ
├── requirements-dev.txt       # 開発依存パッケージ
└── README.md                  # このファイル
```

## セキュリティ考慮事項

### パスワードポリシー
- 最小12文字
- 大文字、小文字、数字、特殊文字を各1文字以上含む
- bcrypt (cost factor 12) でハッシュ化

### JWT
- HS256アルゴリズムで署名
- 秘密鍵は環境変数で管理（64文字以上）
- デフォルト有効期限: 60分

### テナント分離
- 特権テナント (`tenant_privileged`) 以外は自テナントのみアクセス可能
- 全APIでテナントIDを確認

## トラブルシューティング

### Cosmos DB接続エラー

```
Failed to initialize Cosmos DB
```

対処：
1. `.env` ファイルの `COSMOS_DB_CONNECTION_STRING` が正しいか確認
2. ネットワーク接続を確認
3. Cosmos DBアカウントが存在するか確認

### JWT検証エラー

```
Invalid token
```

対処：
1. トークンが期限切れでないか確認
2. `.env` の `JWT_SECRET_KEY` が正しいか確認
3. トークンが正しくヘッダーに設定されているか確認

### パスワードバリデーションエラー

```
Password must be at least 12 characters
```

対処：
- パスワードポリシーに従った文字列を使用
- 大文字、小文字、数字、特殊文字を各1文字以上含める

## 開発ガイドライン

### コーディング規約
- PEP 8に準拠
- 型ヒントを使用
- docstringを記述

### コミット前チェック
```bash
# コードフォーマット
black app/

# インポート整理
isort app/

# リント
flake8 app/

# 型チェック
mypy app/

# テスト
pytest
```

## デプロイ

### Azure App Serviceへのデプロイ

```bash
# Azure CLIでログイン
az login

# デプロイ
az webapp up --name auth-service-app --resource-group rg-management-app
```

環境変数はAzure Portalで設定：
- App Service > 設定 > 構成 > アプリケーション設定

## ライセンス

内部使用のみ

## 関連ドキュメント

- [API設計](../../docs/arch/api/README.md)
- [データモデル設計](../../docs/arch/data/README.md)
- [セキュリティ設計](../../docs/arch/security/README.md)
- [仕様書](../../docs/管理アプリ/Phase1-MVP開発/Specs/03-認証認可サービス-コアAPI.md)
