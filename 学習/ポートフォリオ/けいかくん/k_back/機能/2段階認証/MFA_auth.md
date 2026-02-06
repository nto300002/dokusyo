⏺ MFA認証に関連するファイルと関数の一覧を整理しました。                                                          
                                                                                                                 
  📱 MFA認証関連ファイル一覧                                                                                     
                                                                                                                 
  Backend Core Files                                                                                             
                                                                                                                 
  1. Models (app/models/mfa.py)                                                                                  
                                                                                                                 
  - MFABackupCode クラス (10-27行目)                                                                             
    - mark_as_used() - バックアップコード使用済みマーク                                                          
  - MFAAuditLog クラス (30-42行目)
    - MFA操作の監査ログ

  2. Staff Model (app/models/staff.py)

  MFA関連メソッド:
  - set_mfa_secret(secret: str) (146-149行目) - MFAシークレット暗号化設定
  - get_mfa_secret() -> Optional[str] (151-178行目) - MFAシークレット復号化取得
  - enable_mfa(db, secret, recovery_codes) (180-195行目) - MFA有効化
  - disable_mfa(db) (197-207行目) - MFA無効化
  - get_backup_codes(db) (209-214行目) - バックアップコード取得
  - get_unused_backup_codes(db) (216-224行目) - 未使用バックアップコード取得
  - has_backup_codes_remaining(db) (226-229行目) - バックアップコード残数確認

  3. Schemas (app/schemas/mfa.py)

  - MfaEnrollmentResponse (4-6行目) - MFA登録レスポンス
  - AdminMfaEnableResponse (9-16行目) - 管理者MFA有効化レスポンス

  4. Services (app/services/mfa.py)

  MfaService クラス:
  - enroll(user: Staff) (14-34行目) - TOTPシークレット/QRコード生成
  - verify(user: Staff, totp_code: str) (36-67行目) - TOTPコード検証&MFA有効化
  - verify_totp_code(user: Staff, totp_code: str) (69-114行目) - TOTPコード検証のみ

  5. API Endpoints (app/api/v1/endpoints/mfa.py)

  ユーザー向けエンドポイント:
  - POST /mfa/enroll (29-64行目) - enroll_mfa() - MFA登録開始
  - POST /mfa/verify (67-119行目) - verify_mfa() - TOTP検証&MFA有効化
  - POST /mfa/disable (122-161行目) - disable_mfa() - MFA無効化(パスワード確認要)

  管理者向けエンドポイント:
  - POST /admin/staff/{staff_id}/mfa/enable (168-234行目) - admin_enable_staff_mfa() - スタッフMFA有効化
  - POST /admin/staff/{staff_id}/mfa/disable (237-278行目) - admin_disable_staff_mfa() - スタッフMFA無効化
  - POST /admin/office/mfa/disable-all (281-363行目) - disable_all_office_mfa() - 事業所全スタッフMFA一括無効化
  - POST /admin/office/mfa/enable-all (366-470行目) - enable_all_office_mfa() - 事業所全スタッフMFA一括有効化

  6. Security Core (app/core/security.py)

  暗号化関数:
  - get_encryption_key() (136-141行目) - 暗号化キー取得
  - encrypt_mfa_secret(secret: str) (144-153行目) - MFAシークレット暗号化
  - decrypt_mfa_secret(encrypted_secret: str) (156-171行目) - MFAシークレット復号化

  TOTP関数:
  - generate_totp_secret() (174-176行目) - TOTPシークレット生成
  - generate_totp_uri(email, secret, issuer_name) (179-183行目) - TOTP URI生成
  - generate_qr_code(secret, email, issuer) (186-211行目) - QRコード画像生成
  - verify_totp(secret, token, window) (214-247行目) - TOTPコード検証
  - sanitize_totp_code(code) (250-262行目) - TOTPコード正規化

  リカバリコード関数:
  - generate_recovery_codes(count=10) (265-277行目) - バックアップコード生成
  - hash_recovery_code(code) (280-282行目) - リカバリコードハッシュ化
  - verify_recovery_code(code, hashed_code) (285-292行目) - リカバリコード検証
  - is_recovery_code_format(code) (295-309行目) - リカバリコード形式検証
  - mask_recovery_codes(codes) (376-386行目) - リカバリコードマスキング
  - get_mfa_backup_info(recovery_codes) (389-395行目) - バックアップコード情報取得

  一時トークン関数:
  - create_temporary_token(...) (312-335行目) - MFA検証用一時トークン作成
  - verify_temporary_token(token, expected_type) (338-352行目) - 一時トークン検証
  - verify_temporary_token_with_session(token, expected_type) (355-373行目) - 一時トークン&セッション情報検証

  7. Messages (app/messages/ja.py)

  MFA関連エラーメッセージ (85-95行目):
  - MFA_ALREADY_ENABLED, MFA_NOT_ENROLLED, MFA_INVALID_CODE, etc.

  ---
  Database Migrations

  1. migrations/versions/su6cug3oavuk_create_mfa.py - MFAテーブル作成
  2. migrations/versions/t5u6v7w8x9y0_add_is_mfa_verified_by_user_to_staff.py - ユーザー検証フラグ追加

  ---
  Frontend

  API Client (k_front/lib/api/mfa.ts)

  - mfaApi.adminEnableStaffMfa(staffId) (16-20行目)
  - mfaApi.adminDisableStaffMfa(staffId) (28-32行目)
  - mfaApi.verifyMfaFirstTime(temporaryToken, totpCode) (41-48行目)

  Types (k_front/types/mfa.ts)

  - MfaResponse, MfaEnableResponse, MfaDisableResponse

  ---
  Tests

  1. tests/core/test_mfa_security.py - セキュリティ関数テスト
  2. tests/models/test_mfa_model.py - モデルテスト
  3. tests/api/v1/test_mfa_api.py - APIエンドポイントテスト
  4. tests/api/v1/test_mfa_admin.py - 管理者APIテスト
  5. tests/api/v1/test_mfa_admin_setup_flow.py - セットアップフローテスト
  6. tests/api/v1/test_mfa_verify_error_handling.py - エラーハンドリングテスト

  ---
  Utilities

  - scripts/fix_double_encoded_mfa_secrets.py - 二重エンコードされたシークレット修正スクリプト