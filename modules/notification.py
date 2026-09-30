"""notification — internal service invoked by other modules (never exposed
as a public route beyond the two preference endpoints, per section 4.14). Dispatch
is fire-and-forget from the caller's perspective: other modules must never block
their API response on notification delivery."""

from fastapi import APIRouter, Depends

from database.db import call_fn, call_fn_one, record_to_dict
from deps import AuthUser, require_auth
from envelope import ok
from adapters.notification.sms_adapter import SmsAdapter
from adapters.notification.push_adapter import push_adapter
from adapters.notification.stub_adapters import whatsapp_adapter, email_adapter
from models.notification_model import PatchPreference

sms_adapter = SmsAdapter()


def adapter_for(channel: str):
    return {"sms": sms_adapter, "whatsapp": whatsapp_adapter, "email": email_adapter}.get(channel, push_adapter)


async def dispatch(
    user_id: int,
    template_code: str,
    variables: dict[str, str] | None = None,
    channel_override: str | None = None,
    category: str = "general",
    is_critical: bool = False,
) -> dict | None:
    """Call this from any module after a material state change. Never awaited
    in a way that would fail the caller's response — errors are swallowed."""
    variables = variables or {}
    try:
        row = await call_fn_one(
            "fn_dispatch_notification", [user_id, template_code, variables, channel_override, category, is_critical]
        )
        if row is None:
            return None
        row = record_to_dict(row)
        if row["delivery_status"] == "skipped_by_preference":
            return row

        if row["channel"] == "email":
            to = row["recipient_email"]
        elif row["channel"] == "push":
            to = row["recipient_fcm_token"]
        else:
            to = row["recipient_phone"]
        if not to:
            await call_fn_one("fn_update_notification_delivery", [row["id"], "failed", {"reason": "no_recipient_address"}])
            return row

        body = row.get("body_with_variables") or ""
        for key, value in variables.items():
            body = body.replace("{{" + key + "}}", str(value))

        adapter = adapter_for(row["channel"])
        result = await adapter.send(to, body, variables)
        await call_fn_one(
            "fn_update_notification_delivery", [row["id"], "sent" if result.delivered else "failed", result.provider_response]
        )
        return row
    except Exception as exc:  # notifications must never break the calling workflow
        print("notification dispatch failed:", exc)
        return None


router = APIRouter()


@router.get("/notifications/preferences")
async def get_preferences(user: AuthUser = Depends(require_auth)):
    rows = await call_fn("fn_get_notification_preferences", [user.user_id])
    return ok([record_to_dict(r) for r in rows])


@router.patch("/notifications/preferences")
async def patch_preferences(body: PatchPreference, user: AuthUser = Depends(require_auth)):
    row = await call_fn_one("fn_update_notification_preference", [user.user_id, body.channel, body.category, body.enabled])
    return ok(record_to_dict(row))
