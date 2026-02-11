# 利用サービス設定サービス API 仕様書

## ドキュメント情報

- **バージョン**: 1.0.0
- **最終更新日**: 2024年
- **ステータス**: Draft
- **共通仕様**: [共通API仕様](../../../docs/arch/api/api-specification.md) を参照

---

## 概要

**ベースURL**: `http://localhost:8003/api/v1`

利用サービス設定サービスは、テナントごとのサービス利用設定を管理します。

---

## 1. サービス管理エンドポイント

### 1.1 サービス一覧取得

```http
GET /services
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "data": [
    {
      "id": "service-uuid",
      "name": "ファイル管理サービス",
      "description": "ファイルのアップロード・管理機能を提供",
      "is_active": true,
      "is_mock": true
    }
  ]
}
```

### 1.2 サービス詳細取得

```http
GET /services/{service_id}
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "id": "service-uuid",
  "name": "ファイル管理サービス",
  "description": "ファイルのアップロード・管理機能を提供",
  "api_url": "https://api.example.com/file-management",
  "is_active": true,
  "is_mock": true,
  "roles": [
    {
      "role_code": "admin",
      "role_name": "管理者"
    },
    {
      "role_code": "user",
      "role_name": "ユーザー"
    }
  ]
}
```

---

## 2. テナントサービス管理エンドポイント

### 2.1 テナントのサービス取得

```http
GET /tenants/{tenant_id}/services
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "tenant_id": "tenant-uuid",
  "services": [
    {
      "id": "service-uuid",
      "name": "ファイル管理サービス",
      "assigned_at": "2024-01-15T10:00:00Z",
      "assigned_by": "admin-user-uuid"
    }
  ]
}
```

### 2.2 テナントにサービス割り当て

```http
POST /tenants/{tenant_id}/services
Authorization: Bearer {token}
```

**必要ロール**: 全体管理者

**リクエスト**:

```json
{
  "service_id": "service-uuid"
}
```

**レスポンス** (201):

```json
{
  "tenant_id": "tenant-uuid",
  "service_id": "service-uuid",
  "assigned_at": "2024-01-25T10:00:00Z"
}
```

**エラー** (409):

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Service already assigned to tenant"
  }
}
```

### 2.3 テナントからサービス解除

```http
DELETE /tenants/{tenant_id}/services/{service_id}
Authorization: Bearer {token}
```

**必要ロール**: 全体管理者

**レスポンス** (204): No Content

---

## エンドポイント一覧

| メソッド | エンドポイント                                      | 説明               | 必要ロール |
| -------- | --------------------------------------------------- | ------------------ | ---------- |
| GET      | `/api/v1/services`                                  | サービス一覧       | 閲覧者以上 |
| GET      | `/api/v1/services/{service_id}`                     | サービス詳細       | 閲覧者以上 |
| GET      | `/api/v1/tenants/{tenant_id}/services`              | テナントのサービス | 閲覧者以上 |
| POST     | `/api/v1/tenants/{tenant_id}/services`              | サービス割り当て   | 全体管理者 |
| DELETE   | `/api/v1/tenants/{tenant_id}/services/{service_id}` | サービス解除       | 全体管理者 |

---

## 変更履歴

| バージョン | 日付 | 変更内容                                | 作成者             |
| ---------- | ---- | --------------------------------------- | ------------------ |
| 1.0.0      | 2024 | 初版作成（統合APIドキュメントから分離） | Architecture Agent |
