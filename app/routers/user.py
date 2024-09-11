from fastapi import APIRouter

from app.config import settings
from app.dependencies import (
    ActiveUserDep,
    DBSessionDep
)
from app.schemas.response import BaseResponse
from app.schemas.user import PublicUser, ChangePasswordRequest
from app.utils.auth import ph
from app.utils.gmail import send_email
from app.utils.rand import generate_random_string

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


@router.get("/me")
async def me(user: ActiveUserDep) -> BaseResponse[PublicUser]:
    return BaseResponse(
        success=True,
        msg="ok",
        data=PublicUser(
            id=user.id,
            email=user.email,
            phone_number=user.phone_number,
            first_name=user.first_name,
            last_name=user.last_name,
            expiration_date=user.expiration_date,
        )
    )


@router.post("/reset-password")
async def reset_password(db_session: DBSessionDep, user: ActiveUserDep) -> BaseResponse:
    reset_code = generate_random_string(6)

    user.reset_password_code = reset_code

    await db_session.commit()

    await send_email(
        sender_email=settings.gmail_email,
        sender_password=settings.gmail_password,
        recipient_email=user.email,
        subject="Reset password",
        message_body=f"Reset password code: {reset_code}"
    )

    return BaseResponse(
        success=True,
        msg=f"письмо отправлено на {user.email}"
    )


@router.post("/change-password")
async def change_password(db_session: DBSessionDep, user: ActiveUserDep, req: ChangePasswordRequest) -> BaseResponse:
    if user.reset_password_code != req.reset_code:
        return BaseResponse(
            success=False,
            msg="неверный код"
        )

    user.password = ph.hash(req.new_password)
    user.reset_password_code = None

    await db_session.commit()

    return BaseResponse(
        success=True,
        msg="пароль успешно изменен"
    )
