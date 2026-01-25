# API設計ガイドライン

## 概要

本ドキュメントでは、各マイクロサービスのAPI設計における共通ルールを定義します。

## 基本原則

### RESTful設計

- リソース指向のURL設計
- HTTPメソッドの意味に従った使用
- ステートレスな通信

### 一貫性

- 全サービスで統一されたレスポンス形式
- 共通のエラーハンドリング
- 統一された認証方式

## URL設計

### 基本形式

```
https://{service-host}/api/{version}/{resource}
```

### 命名規則

| 要素 | 規則 | 例 |
|------|------|-----|
| リソース名 | 複数形、ケバブケース | `/api/tenants`, `/api/service-assignments` |
| パスパラメータ | キャメルケース | `/api/tenants/{tenantId}` |
| クエリパラメータ | キャメルケース | `?pageSize=10&sortBy=createdAt` |

### URL例

```
# リソース一覧
GET  /api/tenants

# リソース詳細
GET  /api/tenants/{tenantId}

# リソース作成
POST /api/tenants

# リソース更新
PUT  /api/tenants/{tenantId}

# リソース削除
DELETE /api/tenants/{tenantId}

# サブリソース
GET  /api/tenants/{tenantId}/users
POST /api/tenants/{tenantId}/users
DELETE /api/tenants/{tenantId}/users/{userId}

# アクション（動詞が必要な場合）
POST /api/auth/login
POST /api/auth/verify
POST /api/backups/{backupId}/restore
```

## HTTPメソッド

| メソッド | 用途 | べき等性 | 安全性 |
|---------|------|---------|--------|
| GET | リソース取得 | Yes | Yes |
| POST | リソース作成、アクション実行 | No | No |
| PUT | リソース全体更新 | Yes | No |
| PATCH | リソース部分更新 | No | No |
| DELETE | リソース削除 | Yes | No |

## リクエスト

### ヘッダー

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer {jwt}
X-Request-ID: {uuid}
X-Tenant-ID: {tenantId}  # テナントコンテキストが必要な場合
```

### ページネーション

```http
GET /api/tenants?page=1&pageSize=20&sortBy=createdAt&sortOrder=desc
```

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| page | number | 1 | ページ番号（1始まり） |
| pageSize | number | 20 | 1ページあたりの件数（最大100） |
| sortBy | string | createdAt | ソートフィールド |
| sortOrder | string | desc | ソート順（asc/desc） |

### フィルタリング

```http
GET /api/users?isActive=true&tenantId=tenant-001
GET /api/tenants?search=株式会社
```

## レスポンス

### 成功レスポンス

#### 単一リソース

```json
{
  "data": {
    "id": "tenant-001",
    "name": "サンプルテナント",
    "createdAt": "2026-01-01T00:00:00Z"
  }
}
```

#### リソース一覧

```json
{
  "data": [
    {
      "id": "tenant-001",
      "name": "サンプルテナント1"
    },
    {
      "id": "tenant-002",
      "name": "サンプルテナント2"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 45,
    "totalPages": 3
  }
}
```

#### 作成成功

```json
// HTTP 201 Created
// Location: /api/tenants/tenant-003
{
  "data": {
    "id": "tenant-003",
    "name": "新規テナント",
    "createdAt": "2026-01-24T10:00:00Z"
  }
}
```

#### 削除成功

```json
// HTTP 204 No Content
// (レスポンスボディなし)
```

### エラーレスポンス

```json
{
  "error": {
    "code": "TENANT_NOT_FOUND",
    "message": "指定されたテナントが見つかりません",
    "details": {
      "tenantId": "tenant-999"
    },
    "requestId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### HTTPステータスコード

| コード | 意味 | 使用場面 |
|-------|------|---------|
| 200 | OK | 取得・更新成功 |
| 201 | Created | 作成成功 |
| 204 | No Content | 削除成功 |
| 400 | Bad Request | リクエスト形式エラー |
| 401 | Unauthorized | 認証エラー |
| 403 | Forbidden | 認可エラー |
| 404 | Not Found | リソース未検出 |
| 409 | Conflict | 競合（重複など） |
| 422 | Unprocessable Entity | バリデーションエラー |
| 429 | Too Many Requests | レート制限超過 |
| 500 | Internal Server Error | サーバーエラー |
| 503 | Service Unavailable | サービス一時停止 |

## エラーコード体系

```
{SERVICE}_{CATEGORY}_{SPECIFIC}
```

| サービス | プレフィックス |
|---------|--------------|
| 共通 | COMMON |
| 認証認可 | AUTH |
| テナント管理 | TENANT |
| サービス設定 | SERVICE |

### エラーコード例

| コード | HTTP | 説明 |
|-------|------|------|
| COMMON_VALIDATION_ERROR | 422 | バリデーションエラー |
| COMMON_INTERNAL_ERROR | 500 | 内部エラー |
| AUTH_INVALID_CREDENTIALS | 401 | 認証情報が無効 |
| AUTH_TOKEN_EXPIRED | 401 | トークン期限切れ |
| AUTH_INSUFFICIENT_PERMISSION | 403 | 権限不足 |
| TENANT_NOT_FOUND | 404 | テナント未検出 |
| TENANT_ALREADY_EXISTS | 409 | テナント名重複 |
| TENANT_PRIVILEGED_PROTECTED | 403 | 特権テナント保護 |

## バリデーション

### リクエストバリデーション

```json
// 422 Unprocessable Entity
{
  "error": {
    "code": "COMMON_VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": {
      "fields": [
        {
          "field": "name",
          "message": "名前は必須です"
        },
        {
          "field": "email",
          "message": "メールアドレスの形式が不正です"
        }
      ]
    }
  }
}
```

## 日付形式

- ISO 8601形式を使用
- タイムゾーンはUTC (Z)

```json
{
  "createdAt": "2026-01-24T10:00:00Z",
  "updatedAt": "2026-01-24T15:30:00Z"
}
```

## バージョニング

### 方針

- URLパスでバージョニング
- メジャーバージョンのみ
- 後方互換性を維持

```
/api/v1/tenants
/api/v2/tenants  # 破壊的変更時
```

### 非推奨化

```json
// レスポンスヘッダー
Deprecation: true
Sunset: Sat, 01 Jul 2026 00:00:00 GMT
Link: </api/v2/tenants>; rel="successor-version"
```

## レート制限

### 制限値

| エンドポイント | 制限 | 単位 |
|--------------|------|------|
| 認証 | 10 | リクエスト/分/IP |
| 一般API | 100 | リクエスト/分/ユーザー |
| 一覧取得 | 30 | リクエスト/分/ユーザー |

### レスポンスヘッダー

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706090400
```

### 制限超過時

```json
// HTTP 429 Too Many Requests
{
  "error": {
    "code": "COMMON_RATE_LIMIT_EXCEEDED",
    "message": "リクエスト制限を超過しました",
    "details": {
      "retryAfter": 60
    }
  }
}
```

## OpenAPI仕様

各サービスは OpenAPI 3.0 仕様書を提供します。

```yaml
openapi: 3.0.3
info:
  title: Tenant Management Service API
  version: 1.0.0
  description: テナント管理サービスのAPI仕様
servers:
  - url: https://api.example.com/api/v1
paths:
  /tenants:
    get:
      summary: テナント一覧取得
      security:
        - BearerAuth: []
      responses:
        '200':
          description: 成功
```

## CORS設定

```yaml
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-Request-ID
Access-Control-Max-Age: 86400
```
