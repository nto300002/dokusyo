  # JWT認証関連ファイルとその関数                                                                             
   
  ## 1. app/core/security.py - JWT生成・検証ユーティリティ                                                     

### JWT関連関数

  - create_access_token(subject, expires_delta, expires_delta_seconds, session_type) - アクセストークン生成
  ```py
  def create_access_token(
    subject: Union[str, Any], # この変数は str または Any（任意の型）を受け取る
    expires_delta: timedelta = None,　# timedelta = 2つの日時の差を示す
    expires_delta_seconds: int = None,
    session_type: str = "standard"
  ) -> str:
      now = datetime.now(timezone.utc) 

      if expires_delta_seconds: # ①: 秒単位で正確な時間を管理する
        expire = now + timedelta(seconds=expires_delta_seconds) # seconds = 3600 nowの1時間後
      elif expires_delta:
        expire = now + expires_delta
      else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

      # ①: 
      """
      実際の使用箇所 (auths.py:300-304):
      access_token = create_access_token(
          subject=str(user.id),
          expires_delta_seconds=session_duration,  # 3600秒（1時間）
          session_type=session_type
      )

        ケース別の動作例

      now = datetime.now(timezone.utc)  # 2026-02-05 10:00:00 UTC

      # ケース1: expires_delta_seconds指定（優先度1）
      create_access_token(subject="user123", expires_delta_seconds=3600, expires_delta=timedelta(minutes=30))
      # → expire = 2026-02-05 11:00:00 UTC (1時間後)
      # → expires_delta_secondsが優先され、expires_deltaは無視される

      # ケース2: expires_delta指定のみ（優先度2）
      create_access_token(subject="user123", expires_delta=timedelta(hours=2))
      # → expire = 2026-02-05 12:00:00 UTC (2時間後)

      # ケース3: 両方未指定（優先度3 - デフォルト）
      create_access_token(subject="user123")
      # → expire = 2026-02-05 10:30:00 UTC (30分後)
      # → ACCESS_TOKEN_EXPIRE_MINUTES = 30
      """

      # セッション期間を秒で計算
      session_duration = int((expire - now).total_seconds())

      to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": now,
        "session_type": session_type,
        "session_duration": session_duration
      }
      secret_key = os.getenv("SECRET_KEY", "test_secret_key_for_pytest")
      encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
      return encoded_jwt

  ```
  - create_refresh_token(subject, session_duration, session_type) - リフレッシュトークン生成（jti付き）
  - decode_access_token(token) - アクセストークンデコード
  - create_email_verification_token(email) - メール確認トークン生成
  - verify_email_verification_token(token) - メール確認トークン検証

### パスワード関連

  - verify_password(plain_password, hashed_password) - パスワード検証
  - get_password_hash(password) - パスワードハッシュ化
  - hash_reset_token(token) - リセットトークンのSHA-256ハッシュ化

### 定数

  - ALGORITHM = "HS256"
  - ACCESS_TOKEN_EXPIRE_MINUTES = 30
  - REFRESH_TOKEN_EXPIRE_DAYS = 7
  - EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = 24
  - TEMPORARY_TOKEN_EXPIRE_MINUTES = 10 (MFA用)

---

## 2. app/api/deps.py - 認証依存性関数

### 認証依存性

  - get_db() - DBセッション提供
  - get_current_user(request, db, token) - JWT検証とユーザー取得（Cookie/Header両対応）
    - Cookie (access_token) 優先、次にAuthorizationヘッダー
    - トークンデコード → ユーザーID抽出 → DB検索
    - 削除済み事務所チェック
    - 削除済みスタッフチェック
    - パスワード変更後のトークン無効化チェック (password_changed_at vs iat)
  - get_db_context() - 非同期コンテキストマネージャ（バックグラウンドタスク用）
  - get_current_staff - get_current_userのエイリアス

### 権限チェック依存性

  - require_manager_or_owner(current_staff) - Manager/Ownerのみ許可
  - require_owner(current_staff) - Ownerのみ許可
  - require_app_admin(current_staff) - app_adminのみ許可
  - check_employee_restriction(db, current_staff, resource_type, action_type, resource_id, request_data) -
  Employee制限チェック（承認リクエスト作成）

### 課金チェック依存性

  - require_active_billing(db, current_staff) - 課金ステータスチェック（past_due/canceledの場合402エラー）

### CSRF保護依存性

  - validate_csrf(request) - CSRFトークン検証（Cookie認証の場合のみ）

### OAuth2設定

  - reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

---

## 3. app/schemas/token.py - トークンスキーマ

### Pydanticモデル

  - Token - アクセストークン + リフレッシュトークン
  - TokenData - トークンペイロードデータ（sub）
  - RefreshToken - リフレッシュトークンリクエスト
  - AccessToken - アクセストークンレスポンス
  - MFARequiredResponse - MFA必須レスポンス（temporary_token含む）
  - TokenWithCookie - Cookie認証レスポンス（access_tokenはCookieに設定）
  - TokenRefreshResponse - トークンリフレッシュレスポンス

### パスワードリセット関連

  - ForgotPasswordRequest - パスワードリセット要求
  - ResetPasswordRequest - パスワードリセット実行（パスワード検証付き）
  - PasswordResetResponse - パスワードリセットレスポンス
  - TokenValidityResponse - トークン有効性レスポンス

---

## 4. app/api/v1/endpoints/auths.py - 認証エンドポイント

### 登録・メール確認

  - POST /register-admin - サービス責任者（owner）登録
  - POST /register - 一般スタッフ（employee/manager）登録
  - GET /verify-email - メール確認トークン検証

### ログイン・トークン

  - POST /token - ログイン（username/password + app_admin用passphrase）
    - レート制限: 5/minute (auths.py:169)
    - MFA有効時: temporary_token返却
    - MFA無効時: access_token（Cookie）+ refresh_token返却
    - セッション期間: 常に1時間（3600秒）
    - Cookie設定（環境別）:
        - 開発: SameSite=Lax
      - 本番: SameSite=None; Secure
  - POST /refresh-token - アクセストークンリフレッシュ（リフレッシュトークンブラックリストチェック付き）
  - POST /logout - ログアウト（Cookie削除）

### MFA検証

  - POST /token/verify-mfa - MFAコード検証（ログイン時）
    - TOTPコードまたはリカバリーコード検証
    - リカバリーコード使用時: DBで使用済みマーク
  - POST /mfa/first-time-verify - MFA初回検証（管理者設定後）
    - is_mfa_verified_by_userフラグをTrueに設定

### パスワードリセット

  - POST /forgot-password - パスワードリセット要求
    - レート制限: 設定値に依存 (auths.py:793)
    - トークン生成 → DB保存 → メール送信
    - セキュリティ: メールアドレスの存在を漏らさない
  - GET /verify-reset-token - リセットトークン有効性確認
    - レート制限: 30/minute (auths.py:880)
  - POST /reset-password - パスワードリセット実行
    - レート制限: 10/10minute (auths.py:913)
    - Have I Been Pwned APIでパスワード侵害チェック
    - password_changed_at更新 → 既存トークン無効化

---

## 5. セキュリティ機能

### トークン無効化メカニズム

  1. パスワード変更後の自動無効化 (deps.py:152-172)
    - password_changed_at > token.iat の場合、401エラー
  2. リフレッシュトークンブラックリスト (auths.py:400-411)
    - jti（JWT ID）を使用してブラックリスト化

### Cookie認証セキュリティ

  - HttpOnly: JavaScript からアクセス不可
  - Secure: 本番環境のみHTTPSで送信
  - SameSite: CSRF攻撃対策
  - Domain/Path: スコープ制御

### レート制限（Limiter）

  - ログイン: 5/minute
  - パスワードリセット要求: カスタマイズ可能
  - トークン検証: 30/minute
  - パスワードリセット実行: 10/10minute