from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.db import call_fn_jsonb, call_fn_one, record_to_dict
from app.deps import AuthUser, require_auth, require_role
from app.envelope import ok

router = APIRouter()


class RegisterBody(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    photo_url: str | None = None
    household_relationship: str | None = None
    language_preference: str = "en"


@router.post("/residents")
async def register_resident(body: RegisterBody, user: AuthUser = Depends(require_auth)):
    resident = record_to_dict(await call_fn_one(
        "fn_register_resident", [user.user_id, body.full_name, body.photo_url, body.household_relationship, body.language_preference]
    ))
    me = await call_fn_jsonb("fn_get_resident_me", [user.user_id])
    match = record_to_dict(await call_fn_one("fn_match_resident_to_community", [user.user_id, me["phone"]]))
    return ok({"resident": resident, "community_match": match}, 201)


@router.get("/residents/me")
async def get_me(user: AuthUser = Depends(require_auth)):
    return ok(await call_fn_jsonb("fn_get_resident_me", [user.user_id]))


class PatchMeBody(BaseModel):
    full_name: str | None = None
    photo_url: str | None = None
    household_relationship: str | None = None
    language_preference: str | None = None


@router.patch("/residents/me")
async def patch_me(body: PatchMeBody, user: AuthUser = Depends(require_auth)):
    current = await call_fn_jsonb("fn_get_resident_me", [user.user_id])
    resident = record_to_dict(await call_fn_one("fn_register_resident", [
        user.user_id,
        body.full_name or current.get("full_name"),
        body.photo_url or current.get("photo_url"),
        body.household_relationship or current.get("household_relationship"),
        body.language_preference or current.get("language_preference"),
    ]))
    return ok(resident)


@router.get("/residents/me/dashboard")
async def dashboard(user: AuthUser = Depends(require_auth)):
    return ok(await call_fn_jsonb("fn_get_resident_dashboard", [user.user_id]))


class MembershipRequestBody(BaseModel):
    community_id: int
    method: str  # invite | admin-approval | resident-data-match


@router.post("/residents/membership-requests")
async def request_membership(body: MembershipRequestBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_request_membership", [user.user_id, body.community_id, body.method]))
    return ok(row, 201)


class AccountStateBody(BaseModel):
    account_state: str
    reason: str | None = None


@router.patch("/residents/{resident_id}/account-state")
async def update_account_state(
    resident_id: int, body: AccountStateBody, user: AuthUser = Depends(require_role("community_admin", "platform_admin"))
):
    row = record_to_dict(await call_fn_one("fn_update_resident_account_state", [user.user_id, resident_id, body.account_state, body.reason]))
    return ok(row)


class PrivacyBody(BaseModel):
    phone_visible: bool | None = None
    email_visible: bool | None = None


@router.patch("/residents/me/privacy")
async def update_privacy(body: PrivacyBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_update_privacy", [user.user_id, body.phone_visible, body.email_visible]))
    return ok(row)
