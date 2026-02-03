from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app import crud, models, schemas
from app.api import deps
from app.core.security import (
    create_access_token,
    verify_password,
    generate_totp_secret,
    generate_totp_uri,
    generate_recovery_codes,
)
from app.services.mfa import MfaService
from app.messages import ja

class MFACode(BaseModel):
    totp_code: str

class MFADisableRequest(BaseModel):
    password: str

router = APIRouter()

@router.post("/mfa/enroll", response_model=schemas.MfaEnrollmentResponse, 
            status_code=status.HTTP_200_OK, summary="MFA登録開始", description="MFA登録開始")
async def enroll_mfa(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.Staff = Depends(deps.get_current_user),
) -> schemas.MfaEnrollmentResponse:
    """
    MFA（多要素認証）の登録を開始します。

    - **current_user**: 認証された有効なスタッフユーザー。

    ユーザーがMFAを既に有効にしている場合は、400 Bad Requestエラーを返します。
    成功した場合、TOTP URIとMFAシークレットを含むレスポンスを返します。
    """
    if current_user.mfa_enabled: # すでにMFAが有効な場合例外を返す
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # 400 Bad Request: リクエストの形式が不正
            detail=ja.MFA_ALREADY_ENABLED,
        )

    mfa_service = MfaService(db) # MFAサービスを初期化
    mfa_enrollment_data = await mfa_service.enroll(user=current_user) 

    await db.commit()

    return schemas.MfaEnrollmentResponse(
        secret_key=mfa_enrollment_data["secret_key"],
        qr_code_uri=mfa_enrollment_data["qr_code_uri"],
    )

@router.post(
    "/mfa/verify",
    status_code=status.HTTP_200_OK,
    summary="MFA検証と有効化",
    description="提供されたTOTPコードを検証し、検証が成功した場合にユーザーのMFAを有効化します。",
)
