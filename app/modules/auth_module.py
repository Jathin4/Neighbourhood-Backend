from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.config import settings
from app.db import call_fn, call_fn_one, record_to_dict
from app.deps import AuthUser, require_auth
from app.envelope import ok
from app.security import sign_access_token
from app.adapters.notification.sms_adapter import SmsAdapter

router = APIRouter()
sms_adapter = SmsAdapter()


class SendOtpBody(BaseModel):
    phone: str = Field(min_length=8, max_length=20)


@router.post("/auth/otp/send")
async def send_otp(body: SendOtpBody):
    row = record_to_dict(await call_fn_one("fn_send_otp", [body.phone]))

    # OTP delivery happens before any user account necessarily exists, so this goes
    # straight to the SMS adapter rather than through fn_dispatch_notification (which
    # is keyed on a user_id and preference row that a first-time caller won't have yet).
    await sms_adapter.send(body.phone, settings.sms_template, {"otp": row["otp_plain"]})

    payload = {"phone": body.phone, "expires_at": row["expires_at"]}
    if settings.dev_expose_otp:
        payload["dev_otp"] = row["otp_plain"]
    return ok(payload)


class VerifyOtpBody(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    otp: str = Field(min_length=4, max_length=6)


@router.post("/auth/otp/verify")
async def verify_otp(body: VerifyOtpBody):
    row = record_to_dict(await call_fn_one("fn_verify_otp_and_login", [body.phone, body.otp]))
    access_token = sign_access_token(row["user_id"], row["role"])
    return ok({
        "access_token": access_token,
        "refresh_token": row["refresh_token_plain"],
        "refresh_token_expires_at": row["refresh_token_expires_at"],
        "user": {"id": row["user_id"], "role": row["role"], "is_new_user": row["is_new_user"]},
    })


class RefreshBody(BaseModel):
    refresh_token: str = Field(min_length=10)


@router.post("/auth/token/refresh")
async def refresh_token(body: RefreshBody):
    row = record_to_dict(await call_fn_one("fn_rotate_refresh_token", [body.refresh_token]))
    access_token = sign_access_token(row["user_id"], row["role"])
    return ok({
        "access_token": access_token,
        "refresh_token": row["refresh_token_plain"],
        "refresh_token_expires_at": row["expires_at"],
    })


@router.post("/auth/logout")
async def logout(user: AuthUser = Depends(require_auth)):
    await call_fn("fn_invalidate_session", [user.user_id])
    return ok({"logged_out": True})


class FcmTokenBody(BaseModel):
    fcm_token: str = Field(min_length=1)


@router.post("/auth/fcm-token")
async def set_fcm_token(body: FcmTokenBody, user: AuthUser = Depends(require_auth)):
    await call_fn_one("fn_set_fcm_token", [user.user_id, body.fcm_token])
    return ok({"stored": True})


class ChangePhoneBody(BaseModel):
    new_phone: str = Field(min_length=8, max_length=20)
    otp: str = Field(min_length=4, max_length=6)


@router.post("/auth/change-phone")
async def change_phone(body: ChangePhoneBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_change_phone", [user.user_id, body.new_phone, body.otp]))
    return ok(row)
