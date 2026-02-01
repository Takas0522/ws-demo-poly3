# 単体テスト設計書: 認証認可サービス - コアAPI

**バージョン**: 2.0.0  
**作成日**: 2026-02-01  
**更新日**: 2026-02-01  
**対象仕様**: SPEC-AUTH-001 v1.0.0  
**テストフレームワーク**: pytest 7.4+, pytest-asyncio 0.21+  
**カバレッジ目標**: 行カバレッジ 75%以上, 分岐カバレッジ 70%以上  
**総テストケース数**: 85ケース（Repository: 17, Service: 23, API: 35, 統合: 10, パフォーマンス: 5）

---

## 1. テスト概要

### 1.1 テスト対象

認証認可サービス（auth-service）の以下のコンポーネント：

- **API層** (`app/api/`)
  - 認証API (`auth.py`): ログイン、JWT検証、ログアウト、現在のユーザー情報取得
  - ユーザー管理API (`users.py`): ユーザーCRUD操作

- **サービス層** (`app/services/`)
  - 認証サービス (`auth_service.py`): 認証ロジック、JWT生成・検証、パスワード検証
  - ユーザーサービス (`user_service.py`): ユーザー管理ロジック、バリデーション

- **リポジトリ層** (`app/repositories/`)
  - ユーザーリポジトリ (`user_repository.py`): Cosmos DB操作、ユーザー検索

- **モデル/スキーマ層** (`app/models/`, `app/schemas/`)
  - データモデル、バリデーション

### 1.2 テスト目的

- **機能検証**: 仕様書に記載された全機能が正しく動作することを確認
- **セキュリティ検証**: 認証・認可・テナント分離が適切に機能することを確認
- **品質保証**: ISTQB基準に基づく体系的なテストで品質を担保
- **リグレッション防止**: 将来の変更時に既存機能が壊れないことを保証

### 1.3 テストスコープ

**テスト対象（Phase 1）**:
- ✅ ユーザー認証（ログイン/ログアウト）
- ✅ JWT発行・検証
- ✅ ユーザーCRUD操作
- ✅ テナント分離
- ✅ パスワードポリシー検証
- ✅ エラーハンドリング

**テスト対象外（Phase 2以降）**:
- ⏭ パスワードリセット
- ⏭ 多要素認証 (MFA)
- ⏭ トークンリフレッシュ
- ⏭ Redisトークンブラックリスト
- ⏭ レート制限

---

## 2. テスト環境

### 2.1 必要なツールとライブラリ

| ツール/ライブラリ | バージョン | 用途 |
|-----------------|----------|------|
| pytest | 7.4+ | テストフレームワーク |
| pytest-asyncio | 0.21+ | 非同期テスト |
| pytest-cov | 4.1+ | カバレッジ計測 |
| pytest-mock | 3.11+ | モック機能 |
| httpx | 0.24+ | 非同期HTTPクライアント |
| faker | 18+ | テストデータ生成 |
| freezegun | 1.2+ | 時刻のモック（JWT期限切れテスト用） |
| pytest-benchmark | 4.0+ | パフォーマンス測定 |
| pytest-xdist | 3.3+ | 並列テスト実行 |

### 2.2 モック対象

以下の外部依存をモック化：

| モック対象 | 理由 | モック方法 |
|-----------|------|----------|
| Cosmos DB | 外部依存排除、テスト高速化 | AsyncMock, MagicMock |
| JWT生成/検証 | 実装はライブラリに依存 | パッチまたは実装使用 |
| Application Insights | ログは副作用のみ | Mock |
| bcrypt | 実装使用（高速化のためcost調整可） | 実装使用またはMock |

### 2.3 テストデータ戦略

- **固定データ**: 基本的な正常系テスト用
- **ランダムデータ**: Fakerで生成（境界値、エッジケース）
- **異常データ**: 不正な形式、長さ、文字種のデータ

### 2.4 時刻依存テストの実装方法

時刻に依存するテスト（JWT期限切れ等）は、`freezegun`ライブラリを使用して時刻をモックします。

```python
from freezegun import freeze_time
import pytest

# JWT期限切れテストの実装例
@freeze_time("2026-02-01 10:00:00")
async def test_verify_token_expired():
    """期限切れトークンのテスト"""
    # トークン生成（有効期限: 2026-02-01 11:00:00）
    user = create_test_user()
    token = await auth_service.create_token(user)
    
    # 時刻を2時間進める（期限切れ）
    with freeze_time("2026-02-01 12:00:00"):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_token(token.access_token)
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
```

**時刻モックの方針**:
- JWT有効期限テスト: `freeze_time`デコレータとコンテキストマネージャーを使用
- 測定基準時刻: 2026-02-01 10:00:00（テスト実行日を基準）
- 有効期限: トークン生成から60分（仕様書準拠）

### 2.5 テストの独立性とクリーンアップ戦略

#### 2.5.1 独立性の保証

- **テスト実行順序**: 全テストは任意の順序で実行可能（依存なし）
- **データ分離**: 各テストはモックを使用し、実データベースを共有しない
- **状態の初期化**: 各テスト前にモックがリセットされる（Fixtureのスコープ: function）
- **並列実行**: モック使用により、テストは並列実行可能（`pytest -n auto`）

#### 2.5.2 Fixtureスコープ

| Fixture | スコープ | 理由 |
|---------|---------|------|
| mock_cosmos_client | function | 各テストで独立したモックを使用、状態を共有しない |
| valid_user_data | function | テストごとに独立したデータ、変更の影響を排除 |
| test_client | function | リクエスト間の状態共有を防止 |
| privileged_tenant_user | function | テストごとに独立したユーザーインスタンス |
| regular_tenant_user | function | テストごとに独立したユーザーインスタンス |

#### 2.5.3 クリーンアップ不要の確認

本テストプランでは、外部依存をすべてモックで置き換えているため、テスト後のクリーンアップは不要です。

| 対象 | クリーンアップ | 理由 |
|------|-------------|------|
| Cosmos DB | 不要 | AsyncMock使用、実データベース未使用 |
| Application Insights | 不要 | Mock使用、実ログ送信なし |
| JWT | 不要 | 状態を持たない、トークンはメモリ内のみ |
| Redis（Phase 1未実装） | - | Phase 1では未使用 |

#### 2.5.4 並列実行の方法

```bash
# pytest-xdistを使用した並列実行
pytest tests/ -n auto  # CPUコア数に応じて自動並列化
pytest tests/ -n 4     # 4プロセスで並列実行
```

---

## 3. テスト設計

### 3.1 テスト技法（ISTQB準拠）

#### 3.1.1 同値分割法（Equivalence Partitioning）

**適用箇所**: パスワード検証、ユーザー名検証、メールアドレス検証

| 入力 | 有効同値クラス | 無効同値クラス |
|-----|-------------|-------------|
| パスワード長 | 12-128文字 | 0-11文字, 129文字以上 |
| パスワード文字種 | 大小英数字+特殊文字 | 大文字のみ、小文字のみ、数字のみ |
| ユーザー名長 | 3-64文字 | 0-2文字, 65文字以上 |
| メールアドレス | 有効形式 | 無効形式（@なし、ドメインなし） |

#### 3.1.2 境界値分析（Boundary Value Analysis）

| 入力項目 | 境界値 |
|---------|-------|
| パスワード長 | 11, 12, 13 / 127, 128, 129 |
| ユーザー名長 | 2, 3, 4 / 63, 64, 65 |
| ページネーション（skip） | -1, 0, 1 |
| ページネーション（limit） | 0, 1, 100, 1000, 1001 |
| JWT有効期限 | 期限直前、期限ちょうど、期限直後 |

#### 3.1.3 デシジョンテーブル（Decision Table）

**ログイン認証のデシジョンテーブル**:

| 条件 | TC1 | TC2 | TC3 | TC4 | TC5 | TC6 | TC7 | TC8 |
|------|-----|-----|-----|-----|-----|-----|-----|-----|
| ユーザー存在 | Y | Y | Y | Y | N | N | N | N |
| パスワード一致 | Y | Y | N | N | - | - | - | - |
| アカウント有効 | Y | N | Y | N | - | - | - | - |
| **結果** | 成功 | 403 | 401 | 401 | 401 | 401 | 401 | 401 |

#### 3.1.4 状態遷移テスト（State Transition Testing）

**ユーザーアカウント状態遷移**:

```
[未作成] --create--> [有効]
[有効] --update(is_active=false)--> [無効]
[無効] --update(is_active=true)--> [有効]
[有効/無効] --delete--> [削除済み]
```

テストケース:
- 有効 → 無効 → 有効（再有効化）
- 有効 → 削除
- 無効 → 削除

---

## 4. テストケース定義

### 4.1 Repository層テスト（test_repository_user.py）

#### 4.1.1 UserRepository - CRUD操作

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| REPO-001 | create: 正常なユーザー作成 | 正常系 | 高 | ユーザーが作成され、IDが返却される |
| REPO-002 | create: Cosmos DBエラー時の例外処理 | 異常系 | 高 | CosmosHttpResponseErrorが発生 |
| REPO-003 | get: 存在するユーザー取得 | 正常系 | 高 | ユーザーオブジェクトが返却される |
| REPO-004 | get: 存在しないユーザー取得 | 異常系 | 高 | Noneが返却される |
| REPO-005 | get: 不正なテナントIDでアクセス | 異常系 | 高 | Noneが返却される |
| REPO-006 | update: ユーザー情報更新 | 正常系 | 中 | 更新されたユーザーが返却される |
| REPO-007 | update: 存在しないユーザー更新 | 異常系 | 中 | ValueErrorが発生 |
| REPO-008 | delete: ユーザー削除 | 正常系 | 中 | 削除成功（戻り値なし） |
| REPO-009 | delete: 存在しないユーザー削除 | 異常系 | 中 | 例外が発生 |

#### 4.1.2 UserRepository - 検索操作

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| REPO-010 | find_by_username: ユーザー名で検索成功 | 正常系 | 高 | ユーザーが返却される |
| REPO-011 | find_by_username: 存在しないユーザー名 | 異常系 | 高 | Noneが返却される |
| REPO-012 | find_by_username: クロスパーティションクエリ | 正常系 | 高 | 全テナントから検索される |
| REPO-013 | find_by_email: メールアドレスで検索成功 | 正常系 | 中 | ユーザーが返却される |
| REPO-014 | find_by_email: テナント内スコープ確認 | 正常系 | 中 | 指定テナント内のみ検索 |
| REPO-015 | list_by_tenant: テナント内ユーザー一覧 | 正常系 | 中 | ユーザーリストが返却される |
| REPO-016 | list_by_tenant: ページネーション動作 | 正常系 | 中 | skip/limitが正しく動作 |
| REPO-017 | list_by_tenant: 空のテナント | 異常系 | 低 | 空配列が返却される |

### 4.2 Service層テスト - AuthService（test_service_auth.py）

#### 4.2.1 認証ロジック

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| AUTH-001 | authenticate: 正常な認証 | 正常系 | 高 | Userオブジェクトが返却される |
| AUTH-002 | authenticate: 不正なパスワード | 異常系 | 高 | Noneが返却される |
| AUTH-003 | authenticate: 存在しないユーザー | 異常系 | 高 | Noneが返却される |
| AUTH-004 | authenticate: 無効化されたアカウント | 異常系 | 高 | Noneが返却される |
| AUTH-005 | authenticate: タイミング攻撃対策（成功/失敗の時間差） | セキュリティ | 高 | 成功時と失敗時の処理時間差が50ms以内、最小処理時間200ms以上 |
| AUTH-006 | authenticate: 例外発生時の処理 | 異常系 | 中 | Noneが返却され、ログ出力 |

**AUTH-005 タイミング攻撃対策テストの実装詳細**:

```python
import time
import statistics
import pytest

async def test_authenticate_timing_attack_resistance():
    """タイミング攻撃対策テスト
    
    検証内容:
    1. 認証成功時と失敗時の処理時間差が50ms以内であること
    2. 最小処理時間が200ms以上であること（意図的な遅延）
    
    測定方法:
    - time.perf_counter()を使用して高精度測定
    - 各パターンを10回測定して平均を算出
    - 測定環境の影響を考慮して許容誤差を設定
    """
    # 正しいユーザー名・正しいパスワード（認証成功）
    times_success = []
    for _ in range(10):
        start = time.perf_counter()
        result = await auth_service.authenticate("valid_user", "ValidP@ss123")
        times_success.append(time.perf_counter() - start)
        assert result is not None
    
    # 正しいユーザー名・誤ったパスワード（認証失敗）
    times_failure = []
    for _ in range(10):
        start = time.perf_counter()
        result = await auth_service.authenticate("valid_user", "WrongPassword")
        times_failure.append(time.perf_counter() - start)
        assert result is None
    
    # 統計計算
    avg_success = statistics.mean(times_success)
    avg_failure = statistics.mean(times_failure)
    min_time = min(times_success + times_failure)
    
    # 検証1: 処理時間の差が50ms以内
    time_diff = abs(avg_success - avg_failure)
    assert time_diff < 0.05, f"処理時間差が許容値を超過: {time_diff*1000:.2f}ms > 50ms"
    
    # 検証2: 最小処理時間が200ms以上（タイミング攻撃対策の遅延）
    assert min_time >= 0.2, f"最小処理時間が不足: {min_time*1000:.2f}ms < 200ms"
    
    print(f"認証成功平均: {avg_success*1000:.2f}ms, 認証失敗平均: {avg_failure*1000:.2f}ms")
```

**測定基準**:
- **許容誤差**: ±50ms（非同期環境のオーバーヘッドを考慮）
- **測定回数**: 各パターン10回（統計的信頼性を確保）
- **基準値**: 200msの意図的な遅延（仕様書のセキュリティ要件）
- **測定精度**: `time.perf_counter()`による高精度測定（マイクロ秒単位）

#### 4.2.2 JWT操作

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| AUTH-007 | create_token: JWT生成 | 正常系 | 高 | TokenResponseが返却される |
| AUTH-008 | create_token: ペイロード内容検証 | 正常系 | 高 | user_id, tenant_id等が含まれる |
| AUTH-009 | create_token: 有効期限設定 | 正常系 | 高 | expが現在時刻+60分（freezegunで検証） |
| AUTH-010 | create_token: ロール情報（Phase 1は空配列） | 正常系 | 中 | rolesが空配列 |
| AUTH-011 | verify_token: 有効なトークン検証 | 正常系 | 高 | TokenDataが返却される |
| AUTH-012 | verify_token: 期限切れトークン | 異常系 | 高 | HTTPException 401、エラーコード: AUTH_003_TOKEN_EXPIRED |
| AUTH-013 | verify_token: 不正な署名 | 異常系 | 高 | HTTPException 401、エラーコード: AUTH_004_INVALID_TOKEN |
| AUTH-014 | verify_token: 不正な形式 | 異常系 | 中 | HTTPException 401、エラーコード: AUTH_004_INVALID_TOKEN |

**AUTH-009, AUTH-012 時刻依存テストの実装例**:

```python
from freezegun import freeze_time

@freeze_time("2026-02-01 10:00:00")
async def test_create_token_expiration_time():
    """JWT有効期限設定テスト"""
    user = create_test_user()
    token_response = await auth_service.create_token(user)
    
    # JWTをデコード（検証なし）
    payload = jwt.decode(
        token_response.access_token,
        options={"verify_signature": False}
    )
    
    # 有効期限が現在時刻+60分であることを検証
    expected_exp = datetime(2026, 2, 1, 11, 0, 0).timestamp()  # 10:00 + 60分
    assert payload["exp"] == expected_exp

@freeze_time("2026-02-01 10:00:00")
async def test_verify_token_expired():
    """期限切れトークン検証テスト"""
    user = create_test_user()
    token_response = await auth_service.create_token(user)  # 有効期限: 11:00
    
    # 時刻を2時間進める（期限切れ）
    with freeze_time("2026-02-01 12:00:00"):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_token(token_response.access_token)
        
        # ステータスコードとエラーコードを検証
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "AUTH_003_TOKEN_EXPIRED"
        assert "expired" in exc_info.value.detail["message"].lower()
```

#### 4.2.3 パスワード操作

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| AUTH-015 | hash_password: パスワードハッシュ化 | 正常系 | 高 | bcryptハッシュが返却される |
| AUTH-016 | hash_password: 同じパスワードで異なるハッシュ | 正常系 | 高 | salt付きで異なるハッシュ |
| AUTH-017 | verify_password: 正しいパスワード検証 | 正常系 | 高 | Trueが返却される |
| AUTH-018 | verify_password: 誤ったパスワード検証 | 異常系 | 高 | Falseが返却される |

#### 4.2.4 特権テナント

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| AUTH-019 | is_privileged_tenant: 特権テナント判定 | 正常系 | 高 | Trueが返却される |
| AUTH-020 | is_privileged_tenant: 一般テナント判定 | 正常系 | 高 | Falseが返却される |

### 4.3 Service層テスト - UserService（test_service_user.py）

#### 4.3.1 ユーザー作成

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| USER-001 | create_user: 正常なユーザー作成 | 正常系 | 高 | Userが作成される |
| USER-002 | create_user: パスワードハッシュ化確認 | 正常系 | 高 | password_hashが設定される |
| USER-003 | create_user: 弱いパスワード | 異常系 | 高 | ValueError（パスワード要件未達） |
| USER-004 | create_user: 重複ユーザー名 | 異常系 | 高 | ValueError（ユーザー名重複） |
| USER-005 | create_user: 重複メールアドレス（テナント内） | 異常系 | 高 | ValueError（メール重複） |
| USER-006 | create_user: 監査ログ（created_by） | 正常系 | 中 | created_byが設定される |

#### 4.3.2 パスワード強度検証

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| USER-007 | validate_password_strength: 有効なパスワード | 正常系 | 高 | Trueが返却される |
| USER-008 | validate_password_strength: 12文字未満 | 境界値 | 高 | Falseが返却される |
| USER-009 | validate_password_strength: ちょうど12文字 | 境界値 | 高 | Trueが返却される（他条件満たす） |
| USER-010 | validate_password_strength: 大文字なし | 異常系 | 高 | Falseが返却される |
| USER-011 | validate_password_strength: 小文字なし | 異常系 | 高 | Falseが返却される |
| USER-012 | validate_password_strength: 数字なし | 異常系 | 高 | Falseが返却される |
| USER-013 | validate_password_strength: 特殊文字なし | 異常系 | 高 | Falseが返却される |

#### 4.3.3 ユーザー更新・削除

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| USER-014 | update_user: 正常な更新 | 正常系 | 中 | ユーザーが更新される |
| USER-015 | update_user: メール重複チェック | 異常系 | 中 | ValueError（メール重複） |
| USER-016 | update_user: 部分更新（display_nameのみ） | 正常系 | 中 | 指定フィールドのみ更新 |
| USER-017 | update_user: 監査ログ（updated_by） | 正常系 | 低 | updated_byが設定される |
| USER-018 | delete_user: 正常な削除 | 正常系 | 中 | ユーザーが削除される |
| USER-019 | delete_user: ログ記録 | 正常系 | 低 | 削除ログが記録される |

#### 4.3.4 ユーザー取得

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| USER-020 | get_user: 正常な取得 | 正常系 | 中 | Userが返却される |
| USER-021 | get_user: 存在しないユーザー | 異常系 | 中 | Noneが返却される |
| USER-022 | list_users: テナント内一覧 | 正常系 | 中 | ユーザーリストが返却される |
| USER-023 | list_users: ページネーション | 正常系 | 低 | skip/limitが適用される |

### 4.4 API層テスト - 認証API（test_api_auth.py）

#### 4.4.1 ログインAPI

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| API-AUTH-001 | POST /login: 正常なログイン | 正常系 | 高 | 200, access_tokenが返却 |
| API-AUTH-002 | POST /login: 不正なパスワード | 異常系 | 高 | 401, エラーコード: AUTH_001_INVALID_CREDENTIALS |
| API-AUTH-003 | POST /login: 存在しないユーザー | 異常系 | 高 | 401, エラーコード: AUTH_001_INVALID_CREDENTIALS |
| API-AUTH-004 | POST /login: 無効化されたアカウント | 異常系 | 高 | 403, エラーコード: AUTH_002_ACCOUNT_DISABLED |
| API-AUTH-005 | POST /login: バリデーションエラー（ユーザー名空） | 異常系 | 中 | 422, バリデーションエラー詳細 |
| API-AUTH-006 | POST /login: バリデーションエラー（パスワード空） | 異常系 | 中 | 422, バリデーションエラー詳細 |
| API-AUTH-007 | POST /login: レスポンス形式検証 | 正常系 | 中 | access_token, token_type, expires_in, user |

**エラーレスポンスの検証項目**:

全てのエラーケースで以下を検証します：
1. **ステータスコード**: HTTP標準に準拠
2. **エラーコード**: 仕様書定義のエラーコード（例: AUTH_001_INVALID_CREDENTIALS）
3. **エラーメッセージ**: 日本語の明確なメッセージ
4. **タイムスタンプ**: ISO8601形式
5. **request_id**: 存在する（トレーサビリティ確保）

**実装例**:

```python
async def test_login_invalid_password_error_response():
    """不正なパスワードのエラーレスポンス検証"""
    response = await client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "WrongPassword123!"
    })
    
    # ステータスコード検証
    assert response.status_code == 401
    
    # レスポンス形式検証
    data = response.json()
    assert "code" in data
    assert "message" in data
    assert "timestamp" in data
    assert "request_id" in data
    
    # エラー内容検証
    assert data["code"] == "AUTH_001_INVALID_CREDENTIALS"
    assert "ユーザー名またはパスワードが不正" in data["message"]
    
    # タイムスタンプ形式検証（ISO8601）
    from datetime import datetime
    datetime.fromisoformat(data["timestamp"])  # パースできることを確認
    
    # request_id形式検証
    assert isinstance(data["request_id"], str)
    assert len(data["request_id"]) > 0

async def test_login_account_disabled_error_response():
    """無効化されたアカウントのエラーレスポンス検証"""
    response = await client.post("/api/v1/auth/login", json={
        "username": "inactive_user",
        "password": "ValidP@ssw0rd123"
    })
    
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "AUTH_002_ACCOUNT_DISABLED"
    assert "アカウントが無効化" in data["message"]
```

#### 4.4.2 JWT検証API

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| API-AUTH-008 | POST /verify: 有効なトークン検証 | 正常系 | 高 | 200, TokenPayloadが返却 |
| API-AUTH-009 | POST /verify: 期限切れトークン | 異常系 | 高 | 401, エラーコード: AUTH_003_TOKEN_EXPIRED |
| API-AUTH-010 | POST /verify: 不正な署名 | 異常系 | 高 | 401, エラーコード: AUTH_004_INVALID_TOKEN |
| API-AUTH-011 | POST /verify: Bearerプレフィックスなし | 異常系 | 中 | 401, エラーコード: AUTH_004_INVALID_TOKEN |
| API-AUTH-012 | POST /verify: Authorizationヘッダーなし | 異常系 | 中 | 401, エラーコード: AUTH_004_INVALID_TOKEN |

#### 4.4.3 ログアウトAPI

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| API-AUTH-013 | POST /logout: 正常なログアウト | 正常系 | 中 | 200, 成功メッセージ |
| API-AUTH-014 | POST /logout: トークンなし | 異常系 | 中 | 401, エラーコード: AUTH_004_INVALID_TOKEN |
| API-AUTH-015 | POST /logout: 不正なトークン | 異常系 | 中 | 401, エラーコード: AUTH_004_INVALID_TOKEN |

#### 4.4.4 現在のユーザー情報API

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| API-AUTH-016 | GET /me: 正常なユーザー情報取得 | 正常系 | 高 | 200, UserResponseが返却 |
| API-AUTH-017 | GET /me: トークンなし | 異常系 | 高 | 401, エラーコード: AUTH_004_INVALID_TOKEN |
| API-AUTH-018 | GET /me: 削除済みユーザー | 異常系 | 中 | 404, エラーコード: USER_001_USER_NOT_FOUND |

### 4.5 API層テスト - ユーザー管理API（test_api_users.py）

#### 4.5.1 ユーザー一覧取得API

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| API-USER-001 | GET /users: 正常な一覧取得 | 正常系 | 高 | 200, ユーザーリスト |
| API-USER-002 | GET /users: ページネーション動作 | 正常系 | 中 | skip/limitが適用される（詳細は後述） |
| API-USER-003 | GET /users: テナント分離（特権テナント） | 正常系 | 高 | 全テナントのユーザー取得可能 |
| API-USER-004 | GET /users: テナント分離（一般テナント） | 正常系 | 高 | 自テナントのみ取得可能 |
| API-USER-005 | GET /users: テナント分離違反 | 異常系 | 高 | 403, エラーコード: USER_004_INSUFFICIENT_PERMISSIONS |
| API-USER-006 | GET /users: tenant_idパラメータなし | 異常系 | 中 | 422, バリデーションエラー |

**API-USER-002 ページネーションテストの詳細検証**:

```python
async def test_list_users_pagination():
    """ページネーション動作の詳細検証"""
    # 20件のユーザーを作成
    tenant_id = "tenant-test"
    users = [await create_test_user(tenant_id, f"user{i}") for i in range(20)]
    
    # 検証1: 先頭10件取得
    response1 = await client.get(
        f"/api/v1/users?tenant_id={tenant_id}&skip=0&limit=10"
    )
    assert response1.status_code == 200
    result1 = response1.json()
    assert len(result1) == 10
    
    # 検証2: 次の10件取得
    response2 = await client.get(
        f"/api/v1/users?tenant_id={tenant_id}&skip=10&limit=10"
    )
    assert response2.status_code == 200
    result2 = response2.json()
    assert len(result2) == 10
    
    # 検証3: 重複がないことを確認
    ids1 = {u["id"] for u in result1}
    ids2 = {u["id"] for u in result2}
    assert ids1.isdisjoint(ids2), "ページ間でデータが重複している"
    
    # 検証4: 境界値（limit=1000）
    response3 = await client.get(
        f"/api/v1/users?tenant_id={tenant_id}&skip=0&limit=1000"
    )
    assert response3.status_code == 200
    
    # 検証5: 制限超過（limit=1001）
    response4 = await client.get(
        f"/api/v1/users?tenant_id={tenant_id}&skip=0&limit=1001"
    )
    assert response4.status_code == 422
    
    # 検証6: 負の値（skip=-1）
    response5 = await client.get(
        f"/api/v1/users?tenant_id={tenant_id}&skip=-1&limit=10"
    )
    assert response5.status_code == 422
```

#### 4.5.2 ユーザー詳細取得API

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| API-USER-007 | GET /users/{user_id}: 正常な詳細取得 | 正常系 | 高 | 200, UserResponse |
| API-USER-008 | GET /users/{user_id}: 存在しないユーザー | 異常系 | 高 | 404, エラーコード: USER_001_USER_NOT_FOUND |
| API-USER-009 | GET /users/{user_id}: テナント分離違反 | 異常系 | 高 | 403, エラーコード: USER_004_INSUFFICIENT_PERMISSIONS |
| API-USER-010 | GET /users/{user_id}: 特権テナントの他テナントアクセス | 正常系 | 中 | 200, 他テナントのユーザー取得可能 |

#### 4.5.3 ユーザー作成API

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| API-USER-011 | POST /users: 正常なユーザー作成 | 正常系 | 高 | 201, UserResponse |
| API-USER-012 | POST /users: 弱いパスワード | 異常系 | 高 | 400, エラーコード: USER_005_WEAK_PASSWORD |
| API-USER-013 | POST /users: 重複ユーザー名 | 異常系 | 高 | 409, エラーコード: USER_002_DUPLICATE_USERNAME |
| API-USER-014 | POST /users: 重複メールアドレス | 異常系 | 高 | 409, エラーコード: USER_003_DUPLICATE_EMAIL |
| API-USER-015 | POST /users: 不正なメール形式 | 異常系 | 中 | 422, バリデーションエラー |
| API-USER-016 | POST /users: テナント分離違反 | 異常系 | 高 | 403, エラーコード: USER_004_INSUFFICIENT_PERMISSIONS |
| API-USER-017 | POST /users: バリデーションエラー（パスワード11文字） | 境界値 | 中 | 400, エラーコード: USER_005_WEAK_PASSWORD |
| API-USER-018 | POST /users: バリデーションエラー（パスワード12文字、条件満たす） | 境界値 | 中 | 201, 作成成功 |

#### 4.5.4 ユーザー更新API

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| API-USER-019 | PUT /users/{user_id}: 正常な更新 | 正常系 | 中 | 200, UserResponse |
| API-USER-020 | PUT /users/{user_id}: 部分更新 | 正常系 | 中 | 指定フィールドのみ更新 |
| API-USER-021 | PUT /users/{user_id}: 重複メールアドレス | 異常系 | 中 | 409, エラーコード: USER_003_DUPLICATE_EMAIL |
| API-USER-022 | PUT /users/{user_id}: テナント分離違反 | 異常系 | 中 | 403, エラーコード: USER_004_INSUFFICIENT_PERMISSIONS |
| API-USER-023 | PUT /users/{user_id}: 存在しないユーザー | 異常系 | 低 | 404, エラーコード: USER_001_USER_NOT_FOUND |

#### 4.5.5 ユーザー削除API

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|---------|
| API-USER-024 | DELETE /users/{user_id}: 正常な削除 | 正常系 | 中 | 204, No Content |
| API-USER-025 | DELETE /users/{user_id}: テナント分離違反 | 異常系 | 中 | 403, エラーコード: USER_004_INSUFFICIENT_PERMISSIONS |
| API-USER-026 | DELETE /users/{user_id}: 存在しないユーザー | 異常系 | 低 | 404, エラーコード: USER_001_USER_NOT_FOUND |

### 4.6 統合テスト（test_integration.py）

統合テストでは、複数のコンポーネントを組み合わせたエンドツーエンドのシナリオを検証します。

| ID | テストケース | 分類 | 優先度 | 期待結果 |
|----|------------|------|--------|------|
| INT-001 | エンドツーエンド: ユーザー作成→ログイン→情報取得 | 正常系 | 高 | 一連の操作が成功、データの整合性確認 |
| INT-002 | エンドツーエンド: ログイン→JWT検証→/me | 正常系 | 高 | JWTが正しく機能、ペイロード情報取得可能 |
| INT-003 | テナント分離: 他テナントのユーザーにアクセス（一般テナント） | 異常系 | 高 | 403エラー、テナント分離が機能 |
| INT-004 | アカウント無効化: 無効化→ログイン失敗 | 正常系 | 中 | 403エラー、無効化が即座に反映 |
| INT-005 | 複数テナント: テナントA作成→テナントB作成→各テナントでログイン | 正常系 | 高 | 各テナントで独立して動作、データ混在なし |
| INT-006 | 特権テナント: 特権ユーザーが全テナントにアクセス | 正常系 | 高 | 全テナントのデータ取得可能、権限チェック機能 |
| INT-007 | エラー伝播: Repository例外→Service例外→API例外 | 異常系 | 中 | 適切なエラーレスポンス、エラーコード一貫性 |
| INT-008 | 監査ログ: ユーザー作成→更新→削除のログ記録 | 正常系 | 中 | 全操作がApplication Insightsにログ記録 |
| INT-009 | ユーザー更新: 情報更新→再ログイン→変更確認 | 正常系 | 低 | 更新内容が即座に反映 |
| INT-010 | JWT期限切れ: ログイン→時間経過→JWT期限切れ→再ログイン | 正常系 | 中 | 期限切れトークン拒否、新トークン発行可能 |

**統合テスト実装例**:

```python
async def test_integration_user_lifecycle():
    """統合テスト: ユーザーのライフサイクル全体"""
    # 1. ユーザー作成
    create_response = await client.post("/api/v1/users", json={
        "username": "integration_test_user",
        "email": "integration@test.com",
        "password": "IntegrationP@ss123",
        "display_name": "Integration Test User",
        "tenant_id": "tenant-test"
    })
    assert create_response.status_code == 201
    user_data = create_response.json()
    user_id = user_data["id"]
    
    # 2. ログイン
    login_response = await client.post("/api/v1/auth/login", json={
        "username": "integration_test_user",
        "password": "IntegrationP@ss123"
    })
    assert login_response.status_code == 200
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # 3. ユーザー情報取得
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["id"] == user_id
    assert me_data["username"] == "integration_test_user"
    
    # 4. ユーザー更新
    update_response = await client.put(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"display_name": "Updated Name"}
    )
    assert update_response.status_code == 200
    
    # 5. 更新内容確認
    get_response = await client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert get_response.status_code == 200
    assert get_response.json()["display_name"] == "Updated Name"
    
    # 6. ユーザー削除
    delete_response = await client.delete(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert delete_response.status_code == 204
    
    # 7. 削除確認
    get_deleted_response = await client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert get_deleted_response.status_code == 404

async def test_integration_tenant_isolation():
    """統合テスト: テナント分離の動作確認"""
    # テナントAのユーザー作成とログイン
    user_a = await create_and_login("tenant_a", "user_a")
    # テナントBのユーザー作成とログイン
    user_b = await create_and_login("tenant_b", "user_b")
    
    # テナントAのユーザーがテナントBのユーザーにアクセス試行
    response = await client.get(
        f"/api/v1/users/{user_b['id']}",
        headers={"Authorization": f"Bearer {user_a['token']}"}
    )
    assert response.status_code == 403
    assert response.json()["code"] == "USER_004_INSUFFICIENT_PERMISSIONS"
```

### 4.7 パフォーマンステスト

パフォーマンステストでは、仕様書で定義された応答時間目標を検証します。

**注意**: パフォーマンステストはモック使用の単体テストでは正確に測定できません。実際のCosmos DB接続を使用した統合テスト環境で実施することを推奨します。

#### 4.7.1 応答時間テスト

| ID | テストケース | 目標値（P95） | 優先度 | 期待結果 |
|----|------------|-------------|--------|------|
| PERF-001 | ログインAPI応答時間 | < 500ms | 高 | 100回実行して95パーセンタイルが500ms未満 |
| PERF-002 | JWT検証API応答時間 | < 50ms | 高 | 100回実行して95パーセンタイルが50ms未満 |
| PERF-003 | ユーザー一覧取得応答時間 | < 200ms | 中 | 100回実行して95パーセンタイルが200ms未満 |
| PERF-004 | ユーザー作成API応答時間 | < 200ms | 中 | 100回実行して95パーセンタイルが200ms未満 |
| PERF-005 | ユーザー詳細取得応答時間 | < 100ms | 中 | 100回実行して95パーセンタイルが100ms未満 |

#### 4.7.2 実装例

```python
import time
import numpy as np
import pytest

@pytest.mark.performance
@pytest.mark.integration  # 実DB接続が必要
async def test_performance_login_response_time():
    """ログインAPI応答時間テスト（P95 < 500ms）
    
    注意: このテストは実際のCosmos DB接続が必要です。
    モック環境では実行をスキップします。
    """
    if USE_MOCK:  # モック使用時はスキップ
        pytest.skip("パフォーマンステストは実DB接続が必要")
    
    response_times = []
    
    # 100回のログインリクエストを実行
    for i in range(100):
        start = time.perf_counter()
        response = await client.post("/api/v1/auth/login", json={
            "username": "perf_test_user",
            "password": "ValidP@ssw0rd123"
        })
        elapsed = (time.perf_counter() - start) * 1000  # ミリ秒
        response_times.append(elapsed)
        
        assert response.status_code == 200
    
    # 統計計算
    p50 = np.percentile(response_times, 50)
    p95 = np.percentile(response_times, 95)
    p99 = np.percentile(response_times, 99)
    avg = np.mean(response_times)
    
    # 結果出力
    print(f"\nログインAPI応答時間:")
    print(f"  平均: {avg:.2f}ms")
    print(f"  P50: {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")
    
    # 目標値検証
    assert p95 < 500, f"P95応答時間が目標値を超過: {p95:.2f}ms > 500ms"

@pytest.mark.performance
@pytest.mark.integration
async def test_performance_jwt_verify_response_time():
    """JWT検証API応答時間テスト（P95 < 50ms）"""
    if USE_MOCK:
        pytest.skip("パフォーマンステストは実DB接続が必要")
    
    # トークン取得
    login_response = await client.post("/api/v1/auth/login", json={
        "username": "perf_test_user",
        "password": "ValidP@ssw0rd123"
    })
    token = login_response.json()["access_token"]
    
    response_times = []
    
    # 100回のJWT検証リクエストを実行
    for i in range(100):
        start = time.perf_counter()
        response = await client.post(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        elapsed = (time.perf_counter() - start) * 1000
        response_times.append(elapsed)
        
        assert response.status_code == 200
    
    p95 = np.percentile(response_times, 95)
    print(f"\nJWT検証API応答時間 P95: {p95:.2f}ms")
    
    assert p95 < 50, f"P95応答時間が目標値を超過: {p95:.2f}ms > 50ms"
```

#### 4.7.3 パフォーマンステストの実行方法

```bash
# パフォーマンステストのみ実行（実DB接続環境）
pytest tests/ -m performance -v

# 統合テスト+パフォーマンステスト
pytest tests/ -m "integration or performance" -v

# パフォーマンステストを除外（通常のCI/CD）
pytest tests/ -m "not performance" -v
```

---

## 5. カバレッジ目標

### 5.1 コードカバレッジ目標

| メトリクス | 目標値 | 測定方法 |
|----------|--------|---------|
| 行カバレッジ | **75%以上** | pytest-cov |
| 分岐カバレッジ | **70%以上** | pytest-cov --branch |
| 関数カバレッジ | 80%以上 | pytest-cov |

### 5.2 優先度別カバレッジ

| コンポーネント | 目標カバレッジ |
|-------------|-------------|
| API層 | 85% |
| Service層 | 80% |
| Repository層 | 70% |
| Model/Schema層 | 60% |

### 5.3 カバレッジ測定コマンド

```bash
# カバレッジ測定
pytest --cov=app --cov-report=html --cov-report=term

# 分岐カバレッジ測定
pytest --cov=app --cov-branch --cov-report=html

# カバレッジレポート確認
open htmlcov/index.html
```

---

## 6. リスク分析

### 6.1 テスト実装リスク

| リスク | 影響度 | 発生確率 | 緩和策 |
|-------|--------|---------|--------|
| Cosmos DBモックの複雑性 | 高 | 高 | AsyncMock/MagicMockで簡潔に実装、統合テストで実DBテスト |
| 非同期テストの難易度 | 中 | 中 | pytest-asyncio活用、ドキュメント参照 |
| テストデータ管理の煩雑さ | 中 | 中 | Fixtureで共通化、Fakerで自動生成 |
| JWT検証のテスト | 中 | 低 | 実装を使用、期限切れは時刻操作 |
| カバレッジ目標未達 | 中 | 中 | 段階的に実装、重要部分から優先 |

### 6.2 品質リスク

| リスク | 影響度 | 発生確率 | 緩和策 |
|-------|--------|---------|--------|
| セキュリティ脆弱性の見逃し | 高 | 低 | セキュリティ観点のテスト強化、レビュー実施 |
| テナント分離の不備 | 高 | 低 | テナント分離専用のテストケース多数実装 |
| タイミング攻撃の検証不足 | 中 | 中 | 処理時間の測定テスト実装 |
| パスワードポリシーの抜け漏れ | 中 | 低 | 境界値テスト網羅、同値分割適用 |

### 6.3 運用リスク

| リスク | 影響度 | 発生確率 | 緩和策 |
|-------|--------|---------|--------|
| テスト実行時間の長期化 | 中 | 中 | 並列実行、モック活用 |
| テストメンテナンスコスト | 中 | 高 | テストコードの品質管理、リファクタリング |
| CI/CD統合の課題 | 低 | 低 | GitHub Actions等で自動化 |

---

## 7. テストデータ設計

### 7.1 固定テストデータ（Fixture）

```python
# conftest.py
@pytest.fixture
def valid_user_data():
    """有効なユーザーデータ"""
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "ValidP@ssw0rd123",
        "displayName": "Test User",
        "tenantId": "tenant-test",
    }

@pytest.fixture
def privileged_tenant_user():
    """特権テナントユーザー"""
    return User(
        id="user_privileged_001",
        tenant_id="tenant_privileged",
        username="admin",
        email="admin@system.com",
        password_hash="...",
        display_name="System Admin",
        is_active=True,
    )

@pytest.fixture
def regular_tenant_user():
    """一般テナントユーザー"""
    return User(
        id="user_regular_001",
        tenant_id="tenant-acme",
        username="john.doe",
        email="john@acme.com",
        password_hash="...",
        display_name="John Doe",
        is_active=True,
    )
```

### 7.2 境界値テストデータ

| 項目 | 最小値 | 最小値+1 | 最大値-1 | 最大値 | 最大値+1 |
|------|--------|---------|---------|--------|---------|
| パスワード長 | 11文字 | 12文字 | 127文字 | 128文字 | 129文字 |
| ユーザー名長 | 2文字 | 3文字 | 63文字 | 64文字 | 65文字 |

### 7.3 異常系テストデータ

```python
INVALID_PASSWORDS = [
    "short",                    # 短すぎる
    "nouppercase123!",          # 大文字なし
    "NOLOWERCASE123!",          # 小文字なし
    "NoDigitPassword!",         # 数字なし
    "NoSpecialChar123",         # 特殊文字なし
]

INVALID_EMAILS = [
    "invalid",                  # @なし
    "invalid@",                 # ドメインなし
    "@example.com",             # ローカル部なし
    "invalid@.com",             # 不正なドメイン
]

INVALID_USERNAMES = [
    "ab",                       # 短すぎる
    "a" * 65,                   # 長すぎる
    "user name",                # スペース含む
    "user<script>",             # 不正な文字
]
```

---

## 8. テスト実行計画

### 8.1 テスト実行手順

1. **環境準備**
   ```bash
   cd /workspace/src/auth-service
   pip install -r requirements-dev.txt
   ```

2. **単体テスト実行**
   ```bash
   # 全テスト実行
   pytest tests/ -v
   
   # カバレッジ付き実行
   pytest tests/ --cov=app --cov-report=html --cov-report=term
   
   # 特定テストのみ実行
   pytest tests/test_service_auth.py -v
   ```

3. **カバレッジレポート確認**
   ```bash
   open htmlcov/index.html
   ```

### 8.2 テスト実行順序

| 順序 | テスト対象 | 理由 |
|------|-----------|------|
| 1 | Model/Schema層 | 依存が少ない |
| 2 | Repository層 | Service層の前提 |
| 3 | Service層 | API層の前提 |
| 4 | API層 | 統合的な動作確認 |
| 5 | 統合テスト | エンドツーエンド確認 |

### 8.3 成功基準

- [ ] 全テストが合格（失敗なし）
- [ ] 行カバレッジ 75%以上
- [ ] 分岐カバレッジ 70%以上
- [ ] 高優先度テストケース 100%実装
- [ ] セキュリティテストケース 100%実装

---

## 9. テストコード構成

### 9.1 ファイル構成

```
tests/
├── __init__.py
├── conftest.py                      # 共通Fixture
├── test_models.py                   # Model層テスト
├── test_schemas.py                  # Schema層テスト
├── test_repository_user.py          # UserRepositoryテスト
├── test_service_auth.py             # AuthServiceテスト
├── test_service_user.py             # UserServiceテスト（既存）
├── test_api_auth.py                 # 認証APIテスト（既存）
├── test_api_users.py                # ユーザー管理APIテスト
├── test_integration.py              # 統合テスト
└── TEST_PLAN.md                     # 本ドキュメント
```

### 9.2 命名規則

| 対象 | 命名規則 | 例 |
|------|---------|-----|
| テストクラス | `Test<対象クラス名>` | `TestAuthService` |
| テストメソッド | `test_<機能>_<条件>` | `test_authenticate_success` |
| Fixture | `<説明>_<種類>` | `valid_user_data`, `mock_repository` |

### 9.3 テストコードの品質基準

#### 9.3.1 可読性基準

- **AAAパターン**: Arrange（準備）→ Act（実行）→ Assert（検証）の順序を守る
- **1テスト1検証**: 各テストは1つの機能・条件を検証する（単一責任原則）
- **明確な命名**: テスト名から何をテストしているか明確にわかる
- **コメント**: 複雑なロジックには日本語コメントを追加
- **適切な長さ**: 1テストメソッドは50行以内を目安

#### 9.3.2 保守性基準

- **DRY原則**: 共通処理はFixtureまたはヘルパー関数に抽出
- **マジックナンバー回避**: 定数は名前をつけて定義（例: `MIN_PASSWORD_LENGTH = 12`）
- **適切な抽象化**: テストデータ生成ロジックはFixtureに分離
- **一貫性**: 同じテストパターンには同じ構造を使用

#### 9.3.3 テストコード例

**✅ 良い例**:

```python
# AAAパターンに従い、コメントで区切りを明確化
async def test_create_user_with_valid_data_returns_user_object():
    """有効なデータでユーザー作成すると、Userオブジェクトが返却される
    
    検証内容:
    - ユーザーIDが生成される
    - パスワードがハッシュ化される
    - 入力値が正しく設定される
    """
    # Arrange（準備）
    user_data = UserCreateRequest(
        username="testuser",
        email="test@example.com",
        password="ValidP@ssw0rd123",
        display_name="Test User",
        tenant_id="tenant-test"
    )
    
    # Act（実行）
    result = await user_service.create_user(user_data, created_by="admin")
    
    # Assert（検証）
    assert result.id.startswith("user_")
    assert result.username == "testuser"
    assert result.email == "test@example.com"
    assert result.password_hash != "ValidP@ssw0rd123"  # ハッシュ化されている
    assert result.display_name == "Test User"
    assert result.tenant_id == "tenant-test"

# 境界値は定数で定義
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128

@pytest.mark.parametrize("length", [
    MIN_PASSWORD_LENGTH - 1,  # 境界値-1
    MIN_PASSWORD_LENGTH,      # 境界値
    MAX_PASSWORD_LENGTH,      # 境界値
    MAX_PASSWORD_LENGTH + 1,  # 境界値+1
])
async def test_password_length_validation(length):
    """パスワード長の境界値検証"""
    password = "A1!" + "a" * (length - 3)  # 条件を満たすパスワード生成
    is_valid = await user_service.validate_password_strength(password)
    
    if MIN_PASSWORD_LENGTH <= length <= MAX_PASSWORD_LENGTH:
        assert is_valid is True
    else:
        assert is_valid is False
```

**❌ 悪い例**:

```python
# 何をテストしているか不明、AAAパターン不使用
async def test_user():
    u = await s.c({"username": "t"})  # 略語で可読性が低い
    assert u  # 何を検証しているか不明

# マジックナンバー、コメントなし
async def test_pwd():
    p = "a" * 11  # 11の意味が不明
    assert not validate(p)  # どの条件を検証しているか不明

# 複数の検証を1つのテストに詰め込み
async def test_everything():
    # ユーザー作成、ログイン、更新、削除を全て1つのテストで実施
    user = await create_user(...)
    token = await login(...)
    await update_user(...)
    await delete_user(...)
    # 失敗時にどこで問題が起きたかわかりにくい
```

### 9.4 テストクラス構成例

```python
class TestAuthService:
    """AuthServiceのテスト"""
    
    class Test認証:
        """認証機能のテスト"""
        
        def test_authenticate_正常な認証(self):
            """正常な認証のテスト"""
            # TODO: テスト実装
            pass
        
        def test_authenticate_不正なパスワード(self):
            """不正なパスワードのテスト"""
            # TODO: テスト実装
            pass
    
    class TestJWT:
        """JWT機能のテスト"""
        
        def test_create_token_JWT生成(self):
            """JWT生成のテスト"""
            # TODO: テスト実装
            pass
```

---

## 10. 参照ドキュメント

- [仕様書: 認証認可サービス - コアAPI](../../../docs/管理アプリ/Phase1-MVP開発/Specs/03-認証認可サービス-コアAPI.md)
- [ISTQB Foundation Level Syllabus](https://www.istqb.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)

---

## 11. 更新履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|----------|------|---------|--------|
| 1.0.0 | 2026-02-01 | 初版作成 | システム |
| 2.0.0 | 2026-02-01 | レビュー指摘に基づく改善実施:<br>- ツール追加（freezegun, pytest-benchmark, pytest-xdist）<br>- タイミング攻撃対策テストの具体化（測定方法・実装例追加）<br>- 時刻依存テストの実装方法明確化（freezegun使用）<br>- エラーレスポンス検証項目の追加（エラーコード、メッセージ、形式）<br>- テストの独立性とクリーンアップ戦略を明記<br>- 統合テストを10ケースに拡充<br>- パフォーマンステスト追加（5ケース）<br>- ページネーションテストの検証方法明確化 | システム |

---

**ドキュメント終了**
