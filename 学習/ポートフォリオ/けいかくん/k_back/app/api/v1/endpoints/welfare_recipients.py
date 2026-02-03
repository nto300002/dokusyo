from typing import Any, List
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException # APIRouterは、FastAPIアプリケーションのルーティングを管理するためのクラスです。 
#Dependsは、FastAPIの依存性注入システムを利用するための関数 HTTPExceptionは、HTTPエラーを処理するための例外クラス
from fastapi.responses import JSONResponse # JSONResponseは、FastAPIのレスポンスオブジェクトです。
from psycopg import errors as psycopg_errors # psycopgのエラーを処理するための例外クラス
from sqlalchemy.ext.asyncio import AsyncSession # SQLAlchemyのAsyncSessionクラスです。

from app.api import deps
from app.crud.crud_welfare_recipient import crud_welfare_recipient
from app.models.staff import Staff
from app.models.enums import ResourceType, ActionType
from app.schemas.welfare_recipient import (
    WelfareRecipientResponse,
    WelfareRecipientCreate,
    WelfareRecipientUpdate,
    WelfareRecipientListResponse,
    UserRegistrationRequest,
    UserRegistrationResponse
)
from app.schemas.deadline_alert import DeadlineAlertResponse
from app.services.welfare_recipient_service import WelfareRecipientService
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException
)
from app.messages import ja

router = APIRouter()
logger = logging.getLogger(__name__)

# UserRegistrationResponse  説明: レスポンスのPydantic型（自動バリデーション・シリアライズ）
@router.post("/", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def create_welfare_recipient(
    *, #キーワード専用引数を強制 この後のすべてのパラメータは、名前付きで渡す必要がある
    db: AsyncSession = Depends(deps.get_db), # 依存関数 │ deps.get_db  PostgreSQLデータベースへの非同期接続を提供
    registration_data: UserRegistrationRequest, # HTTPリクエストボディ（JSON) | スキーマ定義: k_back/app/schemas/welfare_recipient.py:187-197 
    current_staff: Staff = Depends(deps.require_active_billing) # JWT認証 + 課金ステータスチェック  参考: k_back/app/api/deps.py  
) -> Any: # 実際のレスポンス: k_back/app/schemas/welfare_recipient.py:200-206  
    """
    包括的なデータで新しい福祉受給者を作成する。
    管理者および所有者のみが受給者を作成できます。
    """
    
    # Check if disability_details has empty category
    for detail in (registration_data.disability_details or []):
        if not detail.category or detail.category.strip() == "":
            raise BadRequestException(ja.RECIPIENT_CATEGORY_MISSING)

    try:
        # Load office associations explicitly to avoid lazy loading issues
        """
        1. リレーション取得: current_staff.office_associations                                                    
        - deps.require_active_billingで既にプリロードされている                                                 
        - getattr()を使って安全に取得（MissingGreenletエラー回避） 
        """
        office_associations = getattr(current_staff, "office_associations", [])
        """
        2. 所属確認:                                                                                              
        - 所属事業所がない場合 → 403 Forbidden                                                                  
        - エラーメッセージ: ja.RECIPIENT_MUST_HAVE_OFFICE 
        """
        if not office_associations or len(office_associations) == 0:
            raise ForbiddenException(ja.RECIPIENT_MUST_HAVE_OFFICE)
        
        office_id = office_associations[0].office_id
        

        # 目的: Employee権限のスタッフは承認リクエストを作成   
        employee_request = await deps.check_employee_restriction(
            db=db,
            current_staff=current_staff,
            resource_type=ResourceType.welfare_recipient,
            action_type=ActionType.create,
            request_data=registration_data.model_dump(mode='json')
        )

        if employee_request:
            # Employee case: return request created response
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "success": True,
                    "message": ja.EMPLOYEE_REQUEST_PENDING,
                    "request_id": None,
                    "support_plan_created": False,
                    "request_id": str(employee_request.id),
                }
            )
        
        # 目的: サービス層で利用者データを一括作成 
        welfare_recipient_id = await WelfareRecipientService.create_recipient_with_details(
            db=db,
            registration_data=registration_data,
            office_id=office_id
        )

        try:
            await db.commit()
        except Exception as commit_error:
            import traceback
            raise

        return UserRegistrationResponse(
            success=True,
            message=ja.RECIPIENT_CREATE_SUCCESS,
            recipient_id=welfare_recipient_id,
            support_plan_created=False,
        )

        except psycopg_errors.InvalidTextRepresentation as e:
            await db.rollback()

            if "disability_category" in str(e):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ja.RECIPIENT_DISABILITY_CATEGORY_MISSING)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ja.RECIPIENT_INVALID_INPUT
            )

        except ValueError as e:
            await db.rollback()
            raise BadRequestException(str(e))
        except HTTPException as e:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise

        import traceback

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ja.RECIPIENT_CREATE_FAILED.format(error=str(e))
        )

        
        
        