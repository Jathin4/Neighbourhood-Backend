import asyncio

from fastapi import APIRouter, Depends

from database.db import call_fn, call_fn_one, record_to_dict
from deps import AuthUser, require_auth
from envelope import ok
from pagination import Pagination, pagination_params, paginated_envelope
from modules.notification import dispatch
from models.notice_model import CreateNoticeBody

router = APIRouter()


@router.post("/notices")
async def create_notice(body: CreateNoticeBody, user: AuthUser = Depends(require_auth)):
    # fn_create_notice re-validates via fn__has_capability('can_create_notice') — community
    # admins/platform admins pass automatically, committee members need the granted capability.
    notice = record_to_dict(await call_fn_one("fn_create_notice", [
        user.user_id, body.community_id, body.title, body.content, body.priority,
        body.attachments, body.audience_type, body.audience_ref, body.expiry_at,
    ]))

    if notice["priority"] == "critical":
        try:
            residents = await call_fn("fn_list_community_resident_ids", [user.user_id, body.community_id])
            await asyncio.gather(*[
                dispatch(
                    r["user_id"], "notice_critical", {"title": notice["title"], "content": notice["content"]},
                    channel_override="push", category="critical", is_critical=True,
                )
                for r in residents
            ])
        except Exception as exc:
            print("critical notice fan-out failed:", exc)

    return ok(notice, 201)


@router.get("/notices")
async def list_notices(user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)):
    rows = [record_to_dict(r) for r in await call_fn("fn_list_notices_for_resident", [user.user_id, pagination.limit, pagination.offset])]
    total = int(rows[0]["total_count"]) if rows else 0
    items = [{k: v for k, v in r.items() if k != "total_count"} for r in rows]
    return ok(paginated_envelope(items, total, pagination))


@router.post("/notices/{notice_id}/read")
async def mark_notice_read(notice_id: int, user: AuthUser = Depends(require_auth)):
    await call_fn("fn_mark_notice_read", [notice_id, user.user_id])
    return ok({"notice_id": notice_id, "read": True})
