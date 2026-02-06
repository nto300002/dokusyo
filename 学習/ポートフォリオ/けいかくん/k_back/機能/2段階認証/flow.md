# ⏺ MFA (多要素認証) 全体フローと実装解説                                                                     
                                                                                                            
  📋 MFA認証の全体フロー                                                                                    
                                                                                                            
  [ユーザー自身による操作フロー]                                                                            
  1. 登録開始 (Enrollment)                                                                                  
     ↓                                                                                                      
  2. 検証 (Verification)                                                                                    
     ↓                                                                                                      
  3. MFA付きログイン (TOTPコード入力)                                                                       
     ↓                                                                                                      
  4. オプション: MFA無効化                                                                                  
                                                                                                            
  [管理者による操作フロー]                                                                                  
  1. 管理者がスタッフのMFAを有効化                                                                          
     ↓                                                                                                      
  2. スタッフがQRコードとリカバリーコードを受け取る                                                         
     ↓                                                                                                      
  3. スタッフは初回使用時に検証が必要                                                                       
     ↓                                                                                                      
  4. オプション: 管理者がMFAを無効化   

## 🔐 1. ユーザー自身による登録: MFA登録開始 (/mfa/enroll)                                                   
  目的: ユーザーがMFA登録を開始し、認証アプリ用のQRコードを取得                                             
                                                                                                            
  コード解説 (k_back/app/api/v1/endpoints/mfa.py:29-64): 

```py
@router.post("/mfa/enroll", response_model=schemas.MfaEnrollmentResponse)
async def enroll_mfa(
    db: AsyncSession = Depends(deps.get_db),
    current_user: Staff = Depends(deps.get_current_user),
) -> Any:

# 主要な処理ステップ:
# 1. MFA既有効化チェック: 
if current_user.is_mfa_enabled:
    raise HTTPException(
        status_code=400,
        detail=ja.MFA_ALREADY_ENABLED
    )

# 2. TOTP秘密鍵とQRコードの生成: 
mfa_data = await MfaService.enroll(db=db, staff=current_user)
"""
- pyotpライブラリを使用して一意の秘密鍵を生成
- 認証アプリ（Google Authenticator、Authyなど）用のQRコード URIを作成
- mfa_secret_keyをデータベースに保存（暗号化）
"""

# 3. レスポンス:
return {                                                                                                  
      "secret_key": mfa_data["secret_key"],  # 手動入力用                                                   
      "qr_code_uri": mfa_data["qr_code_uri"],  # 認証アプリでスキャン                                       
      "message": ja.MFA_ENROLLMENT_SUCCESS                                                                  
  }
```

## ✅ 2. ユーザー自身による検証: MFA検証 (/mfa/verify)
目的: ユーザーがTOTPコードを検証してMFA設定を完了                                                         
                                                                                                            
コード解説 (k_back/app/api/v1/endpoints/mfa.py:67-120): 

```py
@router.post("/mfa/verify", response_model=schemas.MfaVerificationResponse)
async def verify_mfa(
    verification_request: schemas.MfaVerificationRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Staff = Depends(deps.get_current_user)
) -> Any:

# 1. バリデーションチェック: 
if not current_user.mfa_secret_key:
    raise HTTPException(
        status_code=400,
        detail=ja.MFA_NOT_ENROLLED
    )
if current_user.is_mfa_enabled:
    raise HTTPException(
        status_code=400,
        detail=ja.MFA_ALREADY_VERIFIED
    )

# 2. TOTPコードの検証:
is_valid = await mfa_service.verify_totp_code(
    secret_key=current_user.mfa_secret_key,
    totp_code=verification_request.totp_code
)
"""
  - 内部的にpyotp.TOTP(secret_key).verify(totp_code)を使用                                                  
  - 時間ベースの検証（30秒のウィンドウ）                                                                    
  - リプレイアタックを防止
"""

# 3. 検証成功時にMFAを有効化:
current_user.is_mfa_enabled = True
current_user.is_mfa_verified_by_user = True
current_user.mfa_verified_at = datetime.now(timezone.utc)
await db.commit()

# 4. リカバリーコードの生成:
recovery_codes = current_user.generate_recovery_codes()
await db.commit()
return {
    "message": ja.MFA_VERIFICATION_SUCCESS,
    "recovery_codes": recovery_codes  # 10個の使い捨てコード
}
```

⏺ フロントエンド処理を含めた2FA認証の完全フロー                                                             
                                                                                                            
  🔄 全体アーキテクチャ                                                                                     
                                                                                                            
  ┌────────────────────────────────────────────────────────────────────┐                                    
  │                     2FA認証システム全体図                           │                                   
  └────────────────────────────────────────────────────────────────────┘                                    
                                                                                                            
  [フロントエンド (Next.js)]  ←HTTP/JSON→  [バックエンド (FastAPI)]                                         
          ↓                                         ↓                                                       
    React Components                         API Endpoints                                                  
    + State Management                       + JWT + TOTP                                                   
    + Cookie認証                              + Cookie設定                                                  
                                                                                                            
  ---                                                                                                       
  📱 シナリオ1: ユーザー主導のMFA設定フロー                                                                 
                                                                                                            
  ステップ1: MFA登録開始                                                                                    
                                                                                                            
  フロントエンド (k_front/components/auth/MfaSetupForm.tsx:27-50):                                          
                                                                                                            
  // ページ読み込み時に自動的にMFA登録を開始                                                                
  useEffect(() => {                                                                                         
    const enrollMfa = async () => {                                                                         
      const response = await http.post<EnrollResponse>(                                                     
        `/api/v1/auth/mfa/enroll`,                                                                          
        {}                                                                                                  
      );                                                                                                    
      setQrCodeUri(response.qr_code_uri);                                                                   
      setSecretKey(response.secret_key);                                                                    
    };                                                                                                      
    enrollMfa();                                                                                            
  }, [router]);                                                                                             
                                                                                                            
  バックエンド (k_back/app/api/v1/endpoints/mfa.py:35-64):                                                  
                                                                                                            
  @router.post("/mfa/enroll")                                                                               
  async def enroll_mfa(                                                                                     
      db: AsyncSession = Depends(deps.get_db),                                                              
      current_user: Staff = Depends(deps.get_current_user)                                                  
  ):                                                                                                        
      # 1. Cookie認証: deps.get_current_user でJWT検証                                                      
      # 2. MFA既有効化チェック                                                                              
      if current_user.is_mfa_enabled:                                                                       
          raise HTTPException(400, detail=ja.MFA_ALREADY_ENABLED)                                           
                                                                                                            
      # 3. MfaServiceで秘密鍵生成                                                                           
      mfa_data = await MfaService.enroll(db=db, staff=current_user)                                         
      # → pyotp.random_base32() で32文字の秘密鍵生成                                                        
      # → QRコードURI: otpauth://totp/Keikakun:{email}?secret={secret}                                      
                                                                                                            
      return {                                                                                              
          "secret_key": mfa_data["secret_key"],                                                             
          "qr_code_uri": mfa_data["qr_code_uri"]                                                            
      }                                                                                                     
                                                                                                            
  データフロー:                                                                                             
  1. フロントエンド: HTTP POST /api/v1/auth/mfa/enroll (Cookie送信)                                         
  2. バックエンド: Cookie検証 → JWT解析 → ユーザー特定                                                      
  3. バックエンド: pyotp.random_base32() → 秘密鍵生成                                                       
  4. バックエンド: DB保存（暗号化）                                                                         
  5. バックエンド: QRコードURI生成                                                                          
  6. フロントエンド: QRコード表示（qrcode.react）                                                           
                                                                                                            
  フロントエンド UI (k_front/components/auth/MfaSetupForm.tsx:141-145):                                     
                                                                                                            
  <QRCodeCanvas value={qrCodeUri} size={200} />                                                             
  <p className="mt-4">または、以下のキーを手動で入力してください。</p>                                      
  <p className="mt-1 font-mono">{secretKey}</p>                                                             
                                                                                                            
  ---                                                                                                       
  ステップ2: MFA検証（有効化）                                                                              
                                                                                                            
  フロントエンド (k_front/components/auth/MfaSetupForm.tsx:83-108):                                         
                                                                                                            
  const handleSubmit = async (e: React.FormEvent) => {                                                      
    e.preventDefault();                                                                                     
                                                                                                            
    try {                                                                                                   
      // 認証アプリに表示された6桁コードを送信                                                              
      await http.post<void>(`/api/v1/auth/mfa/verify`,                                                      
        { totp_code: totpCode }                                                                             
      );                                                                                                    
                                                                                                            
      alert('2段階認証が有効になりました。ダッシュボードに戻ります。');                                     
      router.push('/dashboard');                                                                            
                                                                                                            
    } catch (err) {                                                                                         
      setVerifyAttempts(prev => prev + 1);                                                                  
                                                                                                            
      // エラーヒント表示                                                                                   
      if (verifyAttempts >= 1) {                                                                            
        errorMessage += '\n\nヒント: 最新のコードを入力してください（30秒ごとに更新）';                     
      }                                                                                                     
      setError(errorMessage);                                                                               
    }                                                                                                       
  }                                                                                                         
                                                                                                            
  バックエンド (k_back/app/api/v1/endpoints/mfa.py:67-120):                                                 
                                                                                                            
  @router.post("/mfa/verify")                                                                               
  async def verify_mfa(                                                                                     
      verification_request: schemas.MfaVerificationRequest,                                                 
      db: AsyncSession = Depends(deps.get_db),                                                              
      current_user: Staff = Depends(deps.get_current_user)                                                  
  ):                                                                                                        
      # 1. バリデーション                                                                                   
      if not current_user.mfa_secret_key:                                                                   
          raise HTTPException(400, detail=ja.MFA_NOT_ENROLLED)                                              
      if current_user.is_mfa_enabled:                                                                       
          raise HTTPException(400, detail=ja.MFA_ALREADY_VERIFIED)                                          
                                                                                                            
      # 2. TOTP検証                                                                                         
      is_valid = await mfa_service.verify_totp_code(                                                        
          secret_key=current_user.mfa_secret_key,                                                           
          totp_code=verification_request.totp_code                                                          
      )                                                                                                     
      # 内部: pyotp.TOTP(secret_key).verify(totp_code)                                                      
                                                                                                            
      if not is_valid:                                                                                      
          raise HTTPException(400, detail=ja.MFA_INVALID_CODE)                                              
                                                                                                            
      # 3. MFA有効化フラグ設定                                                                              
      current_user.is_mfa_enabled = True                                                                    
      current_user.is_mfa_verified_by_user = True  # ユーザー主導                                           
      current_user.mfa_verified_at = datetime.now(timezone.utc)                                             
      await db.commit()                                                                                     
                                                                                                            
      # 4. リカバリーコード生成（10個）                                                                     
      recovery_codes = current_user.generate_recovery_codes()                                               
      await db.commit()                                                                                     
                                                                                                            
      return {                                                                                              
          "message": ja.MFA_VERIFICATION_SUCCESS,                                                           
          "recovery_codes": recovery_codes  # フロントエンドで表示                                          
      }                                                                                                     
                                                                                                            
  重要ポイント:                                                                                             
  - TOTP検証: 30秒ウィンドウ内で時刻ベースコード検証                                                        
  - リカバリーコード: 10個生成、ハッシュ化して保存（1回のみ使用可能）                                       
  - is_mfa_verified_by_user: ユーザー主導 = True、管理者主導 = False                                        
                                                                                                            
  ---                                                                                                       
  🔐 シナリオ2: MFA有効化ユーザーのログインフロー                                                           
                                                                                                            
  ステップ1: ログイン（メール+パスワード）                                                                  
                                                                                                            
  フロントエンド (k_front/components/auth/LoginForm.tsx:58-127):                                            
                                                                                                            
  const handleSubmit = async (e: React.FormEvent) => {                                                      
    e.preventDefault();                                                                                     
                                                                                                            
    try {                                                                                                   
      const data = await authApi.login({                                                                    
        username: formData.email,                                                                           
        password: formData.password                                                                         
      });                                                                                                   
                                                                                                            
      // 分岐処理                                                                                           
      if (data.requires_mfa_first_setup && data.temporary_token) {                                          
        // ケース1: 管理者が設定したMFAの初回セットアップ                                                   
        tokenUtils.setTemporaryToken(data.temporary_token);                                                 
        sessionStorage.setItem('mfa_qr_code_uri', data.qr_code_uri);                                        
        sessionStorage.setItem('mfa_secret_key', data.secret_key);                                          
        router.push('/auth/mfa-first-setup');                                                               
                                                                                                            
      } else if (data.requires_mfa_verification && data.temporary_token) {                                  
        // ケース2: 通常のMFA検証フロー（ユーザー設定済み）                                                 
        tokenUtils.setTemporaryToken(data.temporary_token);                                                 
        router.push('/auth/mfa-verify');                                                                    
                                                                                                            
      } else {                                                                                              
        // ケース3: MFA無効ユーザー → 直接ログイン成功                                                      
        const currentUser = await authApi.getCurrentUser();                                                 
        router.push('/dashboard');                                                                          
      }                                                                                                     
                                                                                                            
    } catch (err) {                                                                                         
      setError(err.message);                                                                                
    }                                                                                                       
  }                                                                                                         
                                                                                                            
  バックエンド (k_back/app/api/v1/endpoints/auths.py:168-367):                                              
                                                                                                            
  @router.post("/token")                                                                                    
  @limiter.limit("5/minute")  # レート制限: 1分間に5回まで                                                  
  async def login_for_access_token(                                                                         
      response: Response,                                                                                   
      request: Request,                                                                                     
      db: AsyncSession = Depends(deps.get_db),                                                              
      username: str = Form(...),                                                                            
      password: str = Form(...),                                                                            
  ):                                                                                                        
      # 1. メール+パスワード検証                                                                            
      user = await staff_crud.get_by_email(db, email=username)                                              
      if not user or not verify_password(password, user.hashed_password):                                   
          raise HTTPException(401, detail=ja.AUTH_INCORRECT_CREDENTIALS)                                    
                                                                                                            
      if not user.is_email_verified:                                                                        
          raise HTTPException(401, detail=ja.AUTH_EMAIL_NOT_VERIFIED)                                       
                                                                                                            
      # 2. 削除済みチェック                                                                                 
      if user.is_deleted:                                                                                   
          raise HTTPException(403, detail="アカウント削除済み")                                             
                                                                                                            
      # 3. MFA有効化チェック                                                                                
      session_duration = 3600  # 1時間                                                                      
      session_type = "standard"                                                                             
                                                                                                            
      if user.is_mfa_enabled:                                                                               
          # Temporary Token発行（MFA検証用）                                                                
          temporary_token = create_temporary_token(                                                         
              user_id=str(user.id),                                                                         
              token_type="mfa_verify",                                                                      
              session_duration=session_duration,                                                            
              session_type=session_type                                                                     
          )                                                                                                 
                                                                                                            
          # 3-1. 管理者が設定したが、ユーザー未検証の場合                                                   
          if not user.is_mfa_verified_by_user:                                                              
              decrypted_secret = user.get_mfa_secret()                                                      
              qr_code_uri = generate_totp_uri(user.email, decrypted_secret)                                 
                                                                                                            
              return {                                                                                      
                  "requires_mfa_first_setup": True,                                                         
                  "temporary_token": temporary_token,                                                       
                  "qr_code_uri": qr_code_uri,                                                               
                  "secret_key": decrypted_secret,                                                           
                  "message": "管理者がMFAを設定しました",                                                   
                  "session_duration": session_duration                                                      
              }                                                                                             
                                                                                                            
          # 3-2. 通常のMFA検証フロー                                                                        
          return {                                                                                          
              "requires_mfa_verification": True,                                                            
              "temporary_token": temporary_token,                                                           
              "session_duration": session_duration                                                          
          }                                                                                                 
                                                                                                            
      # 4. MFA無効ユーザー → 直接JWT発行                                                                    
      access_token = create_access_token(                                                                   
          subject=str(user.id),                                                                             
          expires_delta_seconds=session_duration,                                                           
          session_type=session_type                                                                         
      )                                                                                                     
                                                                                                            
      # 5. Cookie設定（HttpOnly）                                                                           
      response.set_cookie(                                                                                  
          key="access_token",                                                                               
          value=access_token,                                                                               
          httponly=True,                                                                                    
          secure=is_production,                                                                             
          max_age=session_duration,                                                                         
          samesite="none" if is_production else "lax"                                                       
      )                                                                                                     
                                                                                                            
      return {                                                                                              
          "token_type": "bearer",                                                                           
          "session_duration": session_duration,                                                             
          "message": ja.AUTH_LOGIN_SUCCESS                                                                  
      }                                                                                                     
                                                                                                            
  Temporary Tokenの仕組み:                                                                                  
  # Temporary Tokenは短命JWT（5分有効）                                                                     
  def create_temporary_token(user_id, token_type, session_duration, session_type):                          
      return jwt.encode({                                                                                   
          "sub": user_id,                                                                                   
          "type": token_type,  # "mfa_verify"                                                               
          "exp": datetime.utcnow() + timedelta(minutes=5),                                                  
          "session_duration": session_duration,                                                             
          "session_type": session_type                                                                      
      }, SECRET_KEY, algorithm="HS256")                                                                     
                                                                                                            
  ---                                                                                                       
  ステップ2: MFA検証（ログイン時）                                                                          
                                                                                                            
  フロントエンド (k_front/app/auth/mfa-verify/page.tsx:14-67):                                              
                                                                                                            
  const handleSubmit = async (e: React.FormEvent) => {                                                      
    e.preventDefault();                                                                                     
                                                                                                            
    // LocalStorageからTemporary Token取得                                                                  
    const temporaryToken = tokenUtils.getTemporaryToken();                                                  
    if (!temporaryToken) {                                                                                  
      setError('一時トークンが見つかりません。ログインからやり直してください。');                           
      return;                                                                                               
    }                                                                                                       
                                                                                                            
    try {                                                                                                   
      // MFA検証API呼び出し                                                                                 
      await authApi.verifyMfa({                                                                             
        temporary_token: temporaryToken,                                                                    
        totp_code: totpCode,  // 6桁コード                                                                  
      });                                                                                                   
                                                                                                            
      // 検証成功 → Temporary Token削除                                                                     
      tokenUtils.removeTemporaryToken();                                                                    
                                                                                                            
      // ユーザー情報取得（Cookieで認証済み）                                                               
      const currentUser = await authApi.getCurrentUser();                                                   
                                                                                                            
      // リダイレクト判定                                                                                   
      if (currentUser.role !== 'owner' && !currentUser.office) {                                            
        router.push('/auth/select-office');                                                                 
      } else {                                                                                              
        router.push('/dashboard?hotbar_message=MFA認証成功&hotbar_type=success');                           
      }                                                                                                     
                                                                                                            
    } catch (err) {                                                                                         
      setVerifyAttempts(prev => prev + 1);                                                                  
                                                                                                            
      // エラーヒント追加                                                                                   
      if (verifyAttempts >= 1) {                                                                            
        errorMessage += '\n\nヒント: 認証アプリで最新のコードを確認してください（30秒更新）';               
      }                                                                                                     
      if (verifyAttempts >= 2) {                                                                            
        errorMessage += '\n前のページに戻って再度ログインしてください。';                                   
      }                                                                                                     
      setError(errorMessage);                                                                               
    }                                                                                                       
  }                                                                                                         
                                                                                                            
  バックエンド (k_back/app/api/v1/endpoints/auths.py:455-567):                                              
                                                                                                            
  @router.post("/token/verify-mfa")                                                                         
  async def verify_mfa_for_login(                                                                           
      response: Response,                                                                                   
      db: AsyncSession = Depends(deps.get_db),                                                              
      mfa_data: MFAVerifyRequest,                                                                           
  ):                                                                                                        
      # 1. Temporary Token検証                                                                              
      token_data = verify_temporary_token_with_session(                                                     
          mfa_data.temporary_token,                                                                         
          expected_type="mfa_verify"                                                                        
      )                                                                                                     
      if not token_data:                                                                                    
          raise HTTPException(401, detail=ja.AUTH_INVALID_TEMPORARY_TOKEN)                                  
                                                                                                            
      user_id = token_data["user_id"]                                                                       
      session_duration = token_data["session_duration"]                                                     
      session_type = token_data["session_type"]                                                             
                                                                                                            
      # 2. ユーザー取得                                                                                     
      user = await staff_crud.get(db, id=user_id)                                                           
      if not user or not user.is_mfa_enabled:                                                               
          raise HTTPException(401, detail=ja.AUTH_MFA_NOT_CONFIGURED)                                       
                                                                                                            
      # 3. TOTP検証 OR リカバリーコード検証                                                                 
      verification_successful = False                                                                       
                                                                                                            
      # 3-1. TOTPコード検証                                                                                 
      if mfa_data.totp_code:                                                                                
          decrypted_secret = user.get_mfa_secret()                                                          
          totp_result = verify_totp(                                                                        
              secret=decrypted_secret,                                                                      
              token=mfa_data.totp_code                                                                      
          )                                                                                                 
          # 内部: pyotp.TOTP(secret).verify(token)                                                          
          if totp_result:                                                                                   
              verification_successful = True                                                                
                                                                                                            
      # 3-2. リカバリーコード検証                                                                           
      if mfa_data.recovery_code and not verification_successful:                                            
          from app.models.mfa import MFABackupCode                                                          
                                                                                                            
          # 未使用のリカバリーコードを全取得                                                                
          stmt = select(MFABackupCode).where(                                                               
              MFABackupCode.staff_id == user.id,                                                            
              MFABackupCode.is_used == False                                                                
          )                                                                                                 
          backup_codes = await db.execute(stmt)                                                             
                                                                                                            
          # ハッシュ照合                                                                                    
          for backup_code in backup_codes.scalars().all():                                                  
              if verify_recovery_code(mfa_data.recovery_code, backup_code.code_hash):                       
                  # 使用済みマーク                                                                          
                  backup_code.mark_as_used()                                                                
                  await db.commit()                                                                         
                  verification_successful = True                                                            
                  break                                                                                     
                                                                                                            
      # 4. 検証失敗                                                                                         
      if not verification_successful:                                                                       
          raise HTTPException(401, detail=ja.AUTH_INVALID_MFA_CODE)                                         
                                                                                                            
      # 5. JWT発行（本番のAccess Token）                                                                    
      access_token = create_access_token(                                                                   
          subject=str(user.id),                                                                             
          expires_delta_seconds=session_duration,                                                           
          session_type=session_type                                                                         
      )                                                                                                     
                                                                                                            
      # 6. Cookie設定                                                                                       
      response.set_cookie(                                                                                  
          key="access_token",                                                                               
          value=access_token,                                                                               
          httponly=True,                                                                                    
          secure=is_production,                                                                             
          max_age=session_duration,                                                                         
          samesite="none" if is_production else "lax"                                                       
      )                                                                                                     
                                                                                                            
      return {                                                                                              
          "token_type": "bearer",                                                                           
          "session_duration": session_duration,                                                             
          "message": "MFA認証成功"                                                                          
      }                                                                                                     
                                                                                                            
  ---                                                                                                       
  🔄 完全フローダイアグラム                                                                                 
                                                                                                            
  ┌─────────────────────────────────────────────────────────────────────────┐                               
  │              MFA有効ユーザーのログイン完全フロー                         │                              
  └─────────────────────────────────────────────────────────────────────────┘                               
                                                                                                            
  [ユーザー] → [フロントエンド] → [バックエンド] → [データベース]                                           
                                                                                                            
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                           
  ステップ1: ログイン（メール+パスワード）                                                                  
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                           
                                                                                                            
  1. ユーザー入力                                                                                           
     ↓                                                                                                      
  2. [Frontend] POST /api/v1/auth/token                                                                     
     {username: "user@example.com", password: "pass123"}                                                    
     ↓                                                                                                      
  3. [Backend] メール+パスワード検証                                                                        
     - DB照会: SELECT * FROM staffs WHERE email = ?                                                         
     - verify_password(password, hashed_password)                                                           
     ↓                                                                                                      
  4. [Backend] is_mfa_enabled チェック                                                                      
     ↓                                                                                                      
  5. [Backend] Temporary Token発行                                                                          
     JWT {                                                                                                  
       sub: user_id,                                                                                        
       type: "mfa_verify",                                                                                  
       exp: now + 5分,                                                                                      
       session_duration: 3600,                                                                              
       session_type: "standard"                                                                             
     }                                                                                                      
     ↓                                                                                                      
  6. [Backend] レスポンス返却                                                                               
     {                                                                                                      
       requires_mfa_verification: true,                                                                     
       temporary_token: "eyJhbG..."                                                                         
     }                                                                                                      
     ↓                                                                                                      
  7. [Frontend] Temporary TokenをLocalStorageに保存                                                         
     localStorage.setItem('temporary_token', token)                                                         
     ↓                                                                                                      
  8. [Frontend] MFA検証ページへリダイレクト                                                                 
     router.push('/auth/mfa-verify')                                                                        
                                                                                                            
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                           
  ステップ2: MFA検証（TOTPコード入力）                                                                      
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                           
                                                                                                            
  9. [Frontend] MFA検証ページ表示                                                                           
     <input placeholder="6桁のコード" />                                                                    
     ↓                                                                                                      
  10. ユーザーが認証アプリのコード入力（例: 123456）                                                        
     ↓                                                                                                      
  11. [Frontend] POST /api/v1/auth/token/verify-mfa                                                         
     {                                                                                                      
       temporary_token: "eyJhbG...",                                                                        
       totp_code: "123456"                                                                                  
     }                                                                                                      
     ↓                                                                                                      
  12. [Backend] Temporary Token検証                                                                         
     - jwt.decode(temporary_token)                                                                          
     - type == "mfa_verify" 確認                                                                            
     - 有効期限チェック（5分以内）                                                                          
     ↓                                                                                                      
  13. [Backend] ユーザー取得                                                                                
     SELECT * FROM staffs WHERE id = user_id                                                                
     ↓                                                                                                      
  14. [Backend] TOTP検証                                                                                    
     - decrypted_secret = user.get_mfa_secret()                                                             
     - pyotp.TOTP(decrypted_secret).verify("123456")                                                        
     - 30秒ウィンドウ内で一致確認                                                                           
     ↓                                                                                                      
  15. [Backend] 検証成功 → JWT発行（本番）                                                                  
     access_token = create_access_token(                                                                    
       subject=user_id,                                                                                     
       expires_delta_seconds=3600                                                                           
     )                                                                                                      
     ↓                                                                                                      
  16. [Backend] Cookie設定                                                                                  
     Set-Cookie: access_token=eyJhbG...;                                                                    
                HttpOnly;                                                                                   
                Secure;                                                                                     
                SameSite=None;                                                                              
                Max-Age=3600                                                                                
     ↓                                                                                                      
  17. [Backend] レスポンス返却                                                                              
     {                                                                                                      
       token_type: "bearer",                                                                                
       session_duration: 3600,                                                                              
       message: "MFA認証成功"                                                                               
     }                                                                                                      
     ↓                                                                                                      
  18. [Frontend] Temporary Token削除                                                                        
     localStorage.removeItem('temporary_token')                                                             
     ↓                                                                                                      
  19. [Frontend] ユーザー情報取得（Cookie認証）                                                             
     GET /api/v1/staffs/me                                                                                  
     ↓                                                                                                      
  20. [Frontend] ダッシュボードへリダイレクト                                                               
     router.push('/dashboard')                                                                              
                                                                                                            
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                           
  以降のAPI呼び出し                                                                                         
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                           
                                                                                                            
  21. [Frontend] 全API呼び出し時にCookie自動送信                                                            
     fetch('/api/v1/...', {credentials: 'include'})                                                         
     ↓                                                                                                      
  22. [Backend] deps.get_current_user()                                                                     
     - Cookieからaccess_token取得                                                                           
     - jwt.decode(access_token)                                                                             
     - ユーザー認証                                                                                         
                                                                                                            
  ---                                                                                                       
  🔑 重要な技術的ポイント                                                                                   
                                                                                                            
  1. 二段階認証トークン                                                                                     
  ┌─────────────────┬─────────────────────┬──────────┬──────────────────┐                                   
  │  トークン種別   │        用途         │ 有効期限 │     保存場所     │                                   
  ├─────────────────┼─────────────────────┼──────────┼──────────────────┤                                   
  │ Temporary Token │ MFA検証前の一時認証 │ 5分      │ LocalStorage     │                                   
  ├─────────────────┼─────────────────────┼──────────┼──────────────────┤                                   
  │ Access Token    │ 本番API認証         │ 1時間    │ HttpOnly Cookie  │                                   
  ├─────────────────┼─────────────────────┼──────────┼──────────────────┤                                   
  │ Refresh Token   │ Access Token更新    │ 7日      │ レスポンスボディ │                                   
  └─────────────────┴─────────────────────┴──────────┴──────────────────┘                                   
  2. Cookie設定の詳細                                                                                       
                                                                                                            
  // フロントエンド: API呼び出し時にCookie自動送信                                                          
  fetch('/api/v1/...', {                                                                                    
    credentials: 'include',  // Cookie送信を有効化                                                          
    headers: {                                                                                              
      'Content-Type': 'application/json'                                                                    
    }                                                                                                       
  })                                                                                                        
                                                                                                            
  # バックエンド: Cookie設定                                                                                
  response.set_cookie(                                                                                      
      key="access_token",                                                                                   
      value=access_token,                                                                                   
      httponly=True,        # JavaScriptからアクセス不可（XSS対策）                                         
      secure=is_production, # HTTPS必須（本番環境）                                                         
      max_age=3600,         # 1時間                                                                         
      samesite="none" if is_production else "lax",  # CSRF対策                                              
      domain=cookie_domain  # クロスドメイン対応                                                            
  )                                                                                                         
                                                                                                            
  3. TOTP検証の仕組み                                                                                       
                                                                                                            
  import pyotp                                                                                              
                                                                                                            
  # 登録時                                                                                                  
  secret = pyotp.random_base32()  # 例: "JBSWY3DPEHPK3PXP"                                                  
  totp = pyotp.TOTP(secret)                                                                                 
  qr_uri = totp.provisioning_uri(                                                                           
      name="user@example.com",                                                                              
      issuer_name="Keikakun"                                                                                
  )                                                                                                         
  # → "otpauth://totp/Keikakun:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Keikakun"                    
                                                                                                            
  # 検証時                                                                                                  
  user_input_code = "123456"                                                                                
  is_valid = totp.verify(user_input_code, valid_window=1)                                                   
  # valid_window=1: 前後30秒（合計90秒）のコードを許容                                                      
                                                                                                            
  時間同期の仕組み:                                                                                         
  現在時刻: 2025-02-04 10:30:15                                                                             
                                                                                                            
  ┌──────────────┬──────────────┬──────────────┐                                                            
  │  10:29:30    │  10:30:00    │  10:30:30    │                                                            
  │  (前の窓)    │  (現在の窓)  │  (次の窓)    │                                                            
  │  コード:456  │  コード:123  │  コード:789  │                                                            
  └──────────────┴──────────────┴──────────────┘                                                            
                 ↑                                                                                          
           valid_window=1                                                                                   
      → 456, 123, 789 すべて有効                                                                            
                                                                                                            
  4. リカバリーコードの仕組み                                                                               
                                                                                                            
  # 生成時（models/staff.py）                                                                               
  def generate_recovery_codes(self, count=10):                                                              
      codes = []                                                                                            
      for _ in range(count):                                                                                
          # 16文字のランダムコード生成                                                                      
          code = secrets.token_urlsafe(12)[:16].upper()                                                     
          # ハッシュ化して保存                                                                              
          code_hash = get_password_hash(code)                                                               
                                                                                                            
          backup_code = MFABackupCode(                                                                      
              staff_id=self.id,                                                                             
              code_hash=code_hash,                                                                          
              is_used=False                                                                                 
          )                                                                                                 
          db.add(backup_code)                                                                               
          codes.append(code)                                                                                
                                                                                                            
      return codes  # 平文コードを返す（ユーザーに表示）                                                    
                                                                                                            
  # 検証時                                                                                                  
  def verify_recovery_code(input_code, stored_hash):                                                        
      return verify_password(input_code, stored_hash)                                                       
      # → bcrypt.checkpw()で照合                                                                            
                                                         
