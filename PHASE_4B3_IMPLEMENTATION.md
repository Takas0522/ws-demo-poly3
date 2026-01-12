# Phase 4B-3 Authentication Service Extensions

## 概要

このドキュメントは、Phase 4B-3で実装された認証サービスの拡張機能について説明します。

## 実装された機能

### 1. userType検証（ログイン時）

#### 機能説明
管理会社外ユーザー（`userType='external'`）のログインを拒否する機能です。

#### 実装詳細
- **ファイル**: `app/services/auth.py`
- **メソッド**: `AuthService.login()`
- **動作**:
  - ユーザーのパスワード検証後、`userType`をチェック
  - `userType`が`'external'`の場合、HTTP 401エラーを返す
  - エラーメッセージ: "管理会社外ユーザーはシステムにログインできません"

#### API例
```python
# リクエスト
POST /auth/login
{
  "email": "external@example.com",
  "password": "password123"
}

# レスポンス（エラー）
401 Unauthorized
{
  "detail": "管理会社外ユーザーはシステムにログインできません"
}
```

### 2. 所属テナント一覧取得

#### 機能説明
ユーザーが所属する全テナントの情報を取得し、ログイン応答に含める機能です。

#### 実装詳細

**CosmosDB Service拡張**:
- **ファイル**: `app/services/cosmosdb.py`
- **新規メソッド**:
  - `get_user_tenants(user_id)`: ユーザーの全テナント所属情報を取得
  - `get_tenant_user(user_id, tenant_id)`: 特定のテナント-ユーザー関係を取得
  - `get_tenant_users_container()`: tenant-usersコンテナへのアクセス

**Schema拡張**:
- **ファイル**: `app/schemas/auth.py`
- **新規Schema**:
  - `TenantInfo`: テナント情報（id, name, roles）
  - `SwitchTenantRequest`: テナント切り替えリクエスト

**LoginResponse拡張**:
```python
class LoginResponse(BaseModel):
    tokens: TokenPair
    user: UserProfile
    tenants: List[TenantInfo] = []  # 新規追加
```

#### API例
```python
# リクエスト
POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

# レスポンス（成功）
200 OK
{
  "tokens": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 3600,
    "token_type": "Bearer"
  },
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "display_name": "Test User",
    "status": "active"
  },
  "tenants": [
    {
      "id": "tenant-123",
      "name": "Tenant Alpha",
      "roles": ["admin"]
    },
    {
      "id": "tenant-789",
      "name": "Tenant Beta",
      "roles": ["user"]
    }
  ]
}
```

### 3. GET /auth/me の拡張

#### 機能説明
現在のユーザー情報に加えて、所属テナント一覧と選択中のテナントIDを返します。

#### 実装詳細
- **ファイル**: `app/api/auth.py`
- **エンドポイント**: `GET /auth/me`
- **変更点**:
  - JWTペイロードから`tenants`配列を抽出
  - `TenantInfo`オブジェクトのリストに変換
  - `selected_tenant_id`を含める

#### API例
```python
# リクエスト
GET /auth/me
Headers: Authorization: Bearer <token>

# レスポンス
200 OK
{
  "id": "user-123",
  "email": "user@example.com",
  "display_name": "Test User",
  "tenant_id": "tenant-123",
  "roles": ["admin"],
  "permissions": ["users.read", "users.write"],
  "tenants": [
    {
      "id": "tenant-123",
      "name": "Tenant Alpha",
      "roles": ["admin"]
    },
    {
      "id": "tenant-789",
      "name": "Tenant Beta",
      "roles": ["user"]
    }
  ],
  "selected_tenant_id": "tenant-123"
}
```

### 4. テナント切り替え機能

#### 機能説明
ユーザーが所属する別のテナントに切り替える機能です。

#### 実装詳細
- **ファイル**: `app/api/auth.py`, `app/services/auth.py`
- **新規エンドポイント**: `POST /auth/switch-tenant`
- **動作**:
  1. ユーザーが指定されたテナントに所属しているか確認
  2. 所属していない場合はHTTP 403エラー
  3. 所属している場合は`selectedTenantId`を更新した新しいJWTを発行

**AuthService拡張**:
```python
async def switch_tenant(
    user_id: str, 
    tenant_id: str, 
    current_token_data: Dict[str, Any]
) -> TokenPair:
    # テナント所属確認
    tenant_user = await cosmos_db.get_tenant_user(user_id, tenant_id)
    if not tenant_user:
        raise HTTPException(403, "指定されたテナントに所属していません")
    
    # 新しいJWT発行
    new_token_data = current_token_data.copy()
    new_token_data["selectedTenantId"] = tenant_id
    access_token = create_access_token(new_token_data)
    
    return TokenPair(
        access_token=access_token,
        refresh_token="",  # 既存のrefresh tokenを使用
        expires_in=settings.jwt_expires_in,
        token_type="Bearer"
    )
```

#### API例
```python
# リクエスト
POST /auth/switch-tenant
Headers: Authorization: Bearer <token>
{
  "tenant_id": "tenant-789"
}

# レスポンス（成功）
200 OK
{
  "access_token": "...",
  "expires_in": 3600,
  "token_type": "Bearer"
}

# レスポンス（エラー）
403 Forbidden
{
  "detail": "指定されたテナントに所属していません"
}
```

### 5. JWTペイロード拡張

#### 新規フィールド
JWTペイロードに以下のフィールドが追加されました：

```python
{
  "sub": "user-123",              # 既存
  "email": "user@example.com",    # 既存
  "displayName": "Test User",     # 既存
  "tenantId": "tenant-123",       # 既存
  "roles": ["admin"],             # 既存
  "permissions": [],              # 既存
  
  # 新規追加フィールド
  "userType": "internal",         # 'internal' | 'external'
  "primaryTenantId": "tenant-123", # ユーザーの主テナントID
  "selectedTenantId": "tenant-123", # 現在選択中のテナントID
  "tenants": [                    # 所属テナント一覧
    {
      "id": "tenant-123",
      "name": "Tenant Alpha",
      "roles": ["admin"]
    },
    {
      "id": "tenant-789",
      "name": "Tenant Beta",
      "roles": ["user"]
    }
  ],
  
  # JWT標準フィールド
  "exp": 1234567890,
  "iat": 1234567890,
  "iss": "saas-auth-service",
  "aud": "saas-app",
  "type": "access"
}
```

## データベーススキーマ

### tenant-users コンテナ

```json
{
  "id": "tu-1",
  "userId": "user-123",
  "tenantId": "tenant-123",
  "tenantName": "Tenant Alpha",
  "roles": ["admin"],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

## テスト

### テストカバレッジ

すべての機能に対してユニットテストが実装されています：

1. **userType検証**:
   - `test_external_user_login_rejected`: 外部ユーザーのログイン拒否
   - `test_internal_user_login_allowed`: 内部ユーザーのログイン許可

2. **テナント一覧取得**:
   - `test_login_includes_tenant_list`: ログイン時のテナント一覧取得
   - `test_login_with_no_tenants`: テナント所属なしの場合

3. **JWTペイロード拡張**:
   - `test_jwt_contains_tenant_info`: JWT内のテナント情報検証

4. **テナント切り替え**:
   - `test_switch_to_valid_tenant`: 正常なテナント切り替え
   - `test_switch_to_invalid_tenant`: 不正なテナント切り替えの拒否

5. **CosmosDB拡張**:
   - `test_get_user_tenants`: ユーザーのテナント一覧取得
   - `test_get_tenant_user`: 特定のテナント-ユーザー関係取得
   - `test_get_tenant_user_not_found`: 存在しない関係の処理

### テスト実行

```bash
# 新規追加されたテストのみ実行
pytest tests/test_auth_extensions.py -v

# すべてのテストを実行
pytest tests/ -v

# カバレッジ付きで実行
pytest --cov=app tests/
```

## セキュリティ考慮事項

1. **userType検証**: パスワード検証成功後、アカウントステータスチェックと同時に実行
2. **テナント切り替え**: 必ずテナント所属を確認してからJWT発行
3. **JWT署名**: RS256アルゴリズムを使用（非対称暗号化）
4. **権限分離**: テナントごとにrolesを管理

## 今後の拡張

- [ ] OpenAPI仕様書の自動生成と公開
- [ ] テナント切り替え履歴の監査ログ
- [ ] テナントごとの権限キャッシュ最適化
- [ ] マルチテナントダッシュボードUI対応

## 参照

- [MULTI_TENANT_IMPLEMENTATION.md](https://github.com/Takas0522/ws-demo-poly-integration/blob/main/docs/MULTI_TENANT_IMPLEMENTATION.md)
- [auth-service-api-fastapi.md](https://github.com/Takas0522/ws-demo-poly-integration/blob/main/docs/api/auth-service-api-fastapi.md)
