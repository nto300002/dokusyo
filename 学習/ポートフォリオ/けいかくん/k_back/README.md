# k_back - バックエンド機能一覧

けいかくんのバックエンドAPIの機能一覧と関連ファイル情報をまとめたドキュメント。

> **パス表記について**  
> ファイルパスは `keikakun_app` を作業ディレクトリとして表記しています。

---

## 📋 目次

1. [アーキテクチャ概要](#アーキテクチャ概要)
2. [認証・認可](#認証認可)
3. [ユーザー管理](#ユーザー管理)
4. [課金管理](#課金管理)
5. [福祉受給者管理](#福祉受給者管理)
6. [支援計画管理](#支援計画管理)
7. [カレンダー連携](#カレンダー連携)
8. [メッセージ・通知](#メッセージ通知)
9. [承認ワークフロー](#承認ワークフロー)
10. [その他の機能](#その他の機能)

---

## アーキテクチャ概要

### 技術スタック
- **フレームワーク**: FastAPI
- **言語**: Python 3.12+
- **データベース**: Neon (PostgreSQL)
- **ORM**: SQLAlchemy 2.0 (非同期モード)
- **DBマイグレーション**: Alembic
- **データ検証**: Pydantic V2
- **コンテナ化**: Docker
- **デプロイ先**: Google Cloud Run

### 階層型アーキテクチャ

```
k_back/app/
├── api/v1/endpoints/    # API層（HTTPリクエスト処理）
├── services/            # サービス層（ビジネスロジック）
├── crud/                # CRUD層（データアクセス）
├── models/              # モデル層（DBテーブル定義）
├── schemas/             # スキーマ層（入出力定義）
├── core/                # コア機能（設定、セキュリティ等）
├── db/                  # データベース接続
├── scheduler/           # スケジューラー（バッチ処理）
├── tasks/               # バックグラウンドタスク
├── utils/               # ユーティリティ
└── templates/           # メールテンプレート
```

---

## 認証・認可

### 主要機能
- JWT（JSON Web Token）ベースの認証
- MFA（多要素認証）対応（TOTP、リカバリコード）
- パスワードリセット機能
- メールアドレス確認
- CSRF保護
- レート制限

### 関連ファイル

#### API層
- **パス**: `k_back/app/api/v1/endpoints/auths.py`
- **主要関数**:
  - `register_admin()` - サービス責任者の登録
  - `register_staff()` - 一般スタッフの登録
  - `verify_email()` - メールアドレス確認
  - `login_for_access_token()` - ログイン（トークン発行）
  - `refresh_access_token()` - トークン更新
  - `verify_mfa_for_login()` - MFA検証（ログイン時）
  - `verify_mfa_first_time()` - MFA初回検証
  - `logout()` - ログアウト
  - `forgot_password()` - パスワードリセットリクエスト
  - `verify_reset_token()` - リセットトークン検証
  - `reset_password()` - パスワードリセット実行

- **パス**: `k_back/app/api/v1/endpoints/mfa.py`
- **主要関数**:
  - MFA設定・管理関連のエンドポイント

#### セキュリティコア
- **パス**: `k_back/app/core/security.py`
- **主要関数**:
  - `create_access_token()` - アクセストークン生成
  - `create_refresh_token()` - リフレッシュトークン生成
  - `create_email_verification_token()` - メール確認トークン生成
  - `verify_password()` - パスワード検証
  - `get_password_hash()` - パスワードハッシュ化
  - `hash_reset_token()` - リセットトークンハッシュ化
  - `generate_totp_secret()` - TOTPシークレット生成
  - `generate_totp_uri()` - TOTP URI生成
  - `generate_qr_code()` - QRコード生成
  - `verify_totp()` - TOTP検証
  - `generate_recovery_codes()` - リカバリコード生成
  - `verify_recovery_code()` - リカバリコード検証
  - `encrypt_mfa_secret()` - MFAシークレット暗号化
  - `decrypt_mfa_secret()` - MFAシークレット復号化
  - `create_temporary_token()` - 一時トークン生成
  - `verify_temporary_token()` - 一時トークン検証

#### CSRF保護
- **パス**: `k_back/app/core/csrf.py`

#### パスワード漏洩チェック
- **パス**: `k_back/app/core/password_breach_check.py`

#### レート制限
- **パス**: `k_back/app/core/limiter.py`

#### CRUD層
- **パス**: `k_back/app/crud/crud_staff.py`
- **パス**: `k_back/app/crud/crud_password_reset.py`

#### サービス層
- **パス**: `k_back/app/services/mfa.py`

#### モデル層
- **パス**: `k_back/app/models/staff.py`
- **パス**: `k_back/app/models/mfa.py`

#### 依存性注入
- **パス**: `k_back/app/api/deps.py`
- **主要関数**:
  - `get_current_user()` - 現在のユーザー取得
  - `require_owner()` - オーナー権限必須
  - `require_manager()` - マネージャー権限必須
  - `require_admin()` - 管理者権限必須

---

## ユーザー管理

### 主要機能
- スタッフ情報の取得・更新
- パスワード変更
- メールアドレス変更
- スタッフの削除（アーカイブ化）
- 通知設定管理
- 役割変更リクエスト

### 関連ファイル

#### API層
- **パス**: `k_back/app/api/v1/endpoints/staffs.py`
- **主要関数**:
  - `read_users_me()` - 認証済みユーザー情報取得
  - `update_staff_name()` - スタッフ名更新
  - `change_password()` - パスワード変更
  - `request_email_change()` - メールアドレス変更リクエスト
  - `verify_email_change()` - メールアドレス変更確認
  - `delete_staff()` - スタッフ削除
  - `get_my_notification_preferences()` - 通知設定取得
  - `update_my_notification_preferences()` - 通知設定更新

- **パス**: `k_back/app/api/v1/endpoints/role_change_requests.py`
- **役割変更リクエスト管理**

- **パス**: `k_back/app/api/v1/endpoints/employee_action_requests.py`
- **従業員アクションリクエスト管理**

#### CRUD層
- **パス**: `k_back/app/crud/crud_staff.py`
- **パス**: `k_back/app/crud/crud_role_change_request.py`
- **パス**: `k_back/app/crud/crud_employee_action_request.py`
- **パス**: `k_back/app/crud/crud_archived_staff.py`

#### サービス層
- **パス**: `k_back/app/services/staff_profile_service.py`
- **パス**: `k_back/app/services/role_change_service.py`
- **パス**: `k_back/app/services/employee_action_service.py`

#### モデル層
- **パス**: `k_back/app/models/staff.py`
- **パス**: `k_back/app/models/staff_profile.py`
- **パス**: `k_back/app/models/role_change_request.py`
- **パス**: `k_back/app/models/employee_action_request.py`
- **パス**: `k_back/app/models/archived_staff.py`

---

## 課金管理

### 主要機能
- Stripe連携による課金管理
- サブスクリプション管理
- 課金ステータス確認
- Checkout Session作成
- Customer Portal Session作成
- Webhook処理（サブスク更新、支払い失敗等）

### 関連ファイル

#### API層
- **パス**: `k_back/app/api/v1/endpoints/billing.py`
- **主要関数**:
  - `get_billing_status()` - 課金ステータス取得
  - `create_checkout_session()` - Checkout Session作成
  - `create_portal_session()` - Customer Portal Session作成
  - `stripe_webhook()` - Stripe Webhook受信

#### CRUD層
- **パス**: `k_back/app/crud/crud_billing.py`
- **パス**: `k_back/app/crud/crud_webhook_event.py`

#### サービス層
- **パス**: `k_back/app/services/billing_service.py`

#### モデル層
- **パス**: `k_back/app/models/billing.py`
- **パス**: `k_back/app/models/webhook_event.py`

#### スケジューラー
- **パス**: `k_back/app/scheduler/billing_scheduler.py`

---

## 福祉受給者管理

### 主要機能
- 福祉受給者（サービス利用者）の登録・管理
- 基本情報管理
- 家族情報管理
- 医療情報管理
- 病院受診記録管理
- 雇用情報管理
- サービス履歴管理

### 関連ファイル

#### API層
- **パス**: `k_back/app/api/v1/endpoints/welfare_recipients.py`
- **福祉受給者の総合管理**

#### CRUD層
- **パス**: `k_back/app/crud/crud_welfare_recipient.py`
- **パス**: `k_back/app/crud/crud_family_member.py`
- **パス**: `k_back/app/crud/crud_medical_info.py`
- **パス**: `k_back/app/crud/crud_hospital_visit.py`
- **パス**: `k_back/app/crud/crud_employment.py`
- **パス**: `k_back/app/crud/crud_service_history.py`

#### サービス層
- **パス**: `k_back/app/services/welfare_recipient_service.py`
- **パス**: `k_back/app/services/withdrawal_service.py`

#### モデル層
- **パス**: `k_back/app/models/welfare_recipient.py`

---

## 支援計画管理

### 主要機能
- 支援計画の作成・更新
- アセスメント管理
- 支援計画のステータス管理
- サイクル管理
- モニタリング

### 関連ファイル

#### API層
- **パス**: `k_back/app/api/v1/endpoints/support_plans.py`
- **パス**: `k_back/app/api/v1/endpoints/support_plan_statuses.py`
- **パス**: `k_back/app/api/v1/endpoints/assessment.py`

#### CRUD層
- **パス**: `k_back/app/crud/crud_support_plan.py`

#### サービス層
- **パス**: `k_back/app/services/support_plan_service.py`
- **パス**: `k_back/app/services/assessment_service.py`

#### モデル層
- **パス**: `k_back/app/models/assessment.py`
- **パス**: `k_back/app/models/support_plan_cycle.py`

---

## カレンダー連携

### 主要機能
- Google Calendar連携
- カレンダーアカウント管理
- イベント同期
- スケジューラーによる自動同期

### 関連ファイル

#### API層
- **パス**: `k_back/app/api/v1/endpoints/calendar.py`

#### CRUD層
- **パス**: `k_back/app/crud/crud_calendar_event.py`
- **パス**: `k_back/app/crud/crud_office_calendar_account.py`
- **パス**: `k_back/app/crud/crud_staff_calendar_account.py`

#### サービス層
- **パス**: `k_back/app/services/calendar_service.py`
- **パス**: `k_back/app/services/google_calendar_client.py`

#### モデル層
- **パス**: `k_back/app/models/calendar_events.py`
- **パス**: `k_back/app/models/calendar_account.py`

#### スケジューラー
- **パス**: `k_back/app/scheduler/calendar_sync_scheduler.py`

---

## メッセージ・通知

### 主要機能
- メッセージの送受信
- お知らせ（通知）管理
- プッシュ通知（Web Push）
- メール送信機能
- 問い合わせ管理

### 関連ファイル

#### API層
- **パス**: `k_back/app/api/v1/endpoints/messages.py`
- **パス**: `k_back/app/api/v1/endpoints/notices.py`
- **パス**: `k_back/app/api/v1/endpoints/push_subscriptions.py`
- **パス**: `k_back/app/api/v1/endpoints/inquiries.py`
- **パス**: `k_back/app/api/v1/endpoints/admin_inquiries.py`
- **パス**: `k_back/app/api/v1/endpoints/admin_announcements.py`

#### CRUD層
- **パス**: `k_back/app/crud/crud_message.py`
- **パス**: `k_back/app/crud/crud_notice.py`
- **パス**: `k_back/app/crud/crud_push_subscription.py`
- **パス**: `k_back/app/crud/crud_inquiry.py`

#### メール送信
- **パス**: `k_back/app/core/mail.py`
- **主要関数**:
  - `send_verification_email()` - 確認メール送信
  - その他メール送信機能

#### プッシュ通知
- **パス**: `k_back/app/core/push.py`

#### モデル層
- **パス**: `k_back/app/models/message.py`
- **パス**: `k_back/app/models/notice.py`
- **パス**: `k_back/app/models/push_subscription.py`
- **パス**: `k_back/app/models/inquiry.py`

---

## 承認ワークフロー

### 主要機能
- 承認リクエスト管理
- 役割変更承認
- 従業員アクション承認
- 脱退リクエスト承認

### 関連ファイル

#### API層
- **パス**: `k_back/app/api/v1/endpoints/role_change_requests.py`
- **パス**: `k_back/app/api/v1/endpoints/employee_action_requests.py`
- **パス**: `k_back/app/api/v1/endpoints/withdrawal_requests.py`

#### CRUD層
- **パス**: `k_back/app/crud/crud_approval_request.py`
- **パス**: `k_back/app/crud/crud_role_change_request.py`
- **パス**: `k_back/app/crud/crud_employee_action_request.py`

#### サービス層
- **パス**: `k_back/app/services/role_change_service.py`
- **パス**: `k_back/app/services/employee_action_service.py`
- **パス**: `k_back/app/services/withdrawal_service.py`

#### モデル層
- **パス**: `k_back/app/models/approval_request.py`
- **パス**: `k_back/app/models/role_change_request.py`
- **パス**: `k_back/app/models/employee_action_request.py`

---

## その他の機能

### 事務所管理
- **API**: `k_back/app/api/v1/endpoints/offices.py`
- **API（管理者用）**: `k_back/app/api/v1/endpoints/admin_offices.py`
- **CRUD**: `k_back/app/crud/crud_office.py`
- **モデル**: `k_back/app/models/office.py`

### ダッシュボード
- **API**: `k_back/app/api/v1/endpoints/dashboard.py`
- **CRUD**: `k_back/app/crud/crud_dashboard.py`
- **サービス**: `k_back/app/services/dashboard_service.py`

### 監査ログ
- **API（管理者用）**: `k_back/app/api/v1/endpoints/admin_audit_logs.py`
- **CRUD**: `k_back/app/crud/crud_audit_log.py`
- **CRUD（事務所監査ログ）**: `k_back/app/crud/crud_office_audit_log.py`
- **モデル**: `k_back/app/models/audit_log.py`

### 利用規約同意
- **API**: `k_back/app/api/v1/endpoints/terms.py`
- **CRUD**: `k_back/app/crud/crud_terms_agreement.py`
- **モデル**: `k_back/app/models/terms_agreement.py`

### CSRF保護
- **API**: `k_back/app/api/v1/endpoints/csrf.py`

### クリーンアップスケジューラー
- **パス**: `k_back/app/scheduler/cleanup_scheduler.py`
- **サービス**: `k_back/app/services/cleanup_service.py`

### ストレージ（Cloud Storage）
- **パス**: `k_back/app/core/storage.py`

### 設定
- **パス**: `k_back/app/core/config.py`
- **環境設定管理**

### 例外処理
- **パス**: `k_back/app/core/exceptions.py`

---

## アプリケーションエントリーポイント

### メインアプリケーション
- **パス**: `k_back/app/main.py`
- **主要関数**:
  - `startup_event()` - アプリケーション起動時処理
  - `shutdown_event()` - アプリケーション終了時処理
  - `csrf_protect_exception_handler()` - CSRFエラーハンドラー
  - `validation_exception_handler()` - バリデーションエラーハンドラー

### データベース設定
- **パス**: `k_back/app/db/session.py` - データベースセッション管理
- **パス**: `k_back/app/db/base.py` - ベースモデル定義

---

## テスト

### テストコード配置
- **パス**: `k_back/tests/`

### テスト実行コマンド
```bash
docker exec -it supabase-backend-1 pytest tests/
```

> **注意**: Dockerコマンドは `k_back/supabase-project` ディレクトリから実行する必要があります。

---

## デプロイ設定

### Docker
- **パス**: `k_back/Dockerfile`

### Cloud Build
- **パス**: `k_back/cloudbuild.yml`

---

## その他のユーティリティスクリプト

- `k_back/seed.py` - データベースシードデータ投入
- `k_back/fix_billing_record.py` - 課金レコード修正スクリプト
- `k_back/check_notification_preferences.py` - 通知設定確認スクリプト

---

## メッセージ定義

### 日本語メッセージ
- **パス**: `k_back/app/messages/ja.py`
- ユーザー向けメッセージの一元管理

---

## 列挙型（Enum）

- **パス**: `k_back/app/models/enums.py`
- システム全体で使用される列挙型定義（役割、ステータス等）
