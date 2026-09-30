from fastapi import APIRouter, Depends

from database.db import call_fn_jsonb, call_fn_one, record_to_dict
from deps import AuthUser, require_auth, require_role
from envelope import ok
from models.resident_model import AccountStateBody, MembershipRequestBody, PatchMeBody, PrivacyBody, RegisterBody

router = APIRouter()


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


@router.post("/residents/membership-requests")
async def request_membership(body: MembershipRequestBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_request_membership", [user.user_id, body.community_id, body.method]))
    return ok(row, 201)


@router.patch("/residents/{resident_id}/account-state")
async def update_account_state(
    resident_id: int, body: AccountStateBody, user: AuthUser = Depends(require_role("community_admin", "platform_admin"))
):
    row = record_to_dict(await call_fn_one("fn_update_resident_account_state", [user.user_id, resident_id, body.account_state, body.reason]))
    return ok(row)


@router.patch("/residents/me/privacy")
async def update_privacy(body: PrivacyBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_update_privacy", [user.user_id, body.phone_visible, body.email_visible]))
    return ok(row)
