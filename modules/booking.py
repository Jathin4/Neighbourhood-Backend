from fastapi import APIRouter, Depends, Query

from database.db import call_fn, call_fn_jsonb, call_fn_one, record_to_dict
from deps import AuthUser, require_auth
from envelope import ok
from idempotency import require_idempotency_key
from pagination import Pagination, pagination_params, paginated_envelope
from modules.notification import dispatch
from models.booking_model import CancelBody, CreateBookingBody, RespondBody

router = APIRouter()


async def notify_booking_change(booking: dict):
    await dispatch(booking["resident_user_id"], "booking_status_changed", {"booking_ref": booking["booking_ref"], "status": booking["status"]})


@router.post("/bookings")
async def create_booking(
    body: CreateBookingBody, user: AuthUser = Depends(require_auth), idempotency_key: str = Depends(require_idempotency_key)
):
    booking = record_to_dict(await call_fn_one("fn_create_booking_request", [
        user.user_id, body.provider_id, body.category_id, body.description, body.preferred_time,
        body.location, body.attachments, body.budget_minor, idempotency_key,
    ]))
    return ok(booking, 201)


@router.patch("/bookings/{booking_id}/respond")
async def respond_booking(booking_id: int, body: RespondBody, user: AuthUser = Depends(require_auth)):
    booking = record_to_dict(await call_fn_one("fn_provider_respond_booking", [user.user_id, booking_id, body.action, body.proposed_time, body.note]))
    await notify_booking_change(booking)
    return ok(booking)


@router.patch("/bookings/{booking_id}/confirm")
async def confirm_booking(booking_id: int, user: AuthUser = Depends(require_auth)):
    booking = record_to_dict(await call_fn_one("fn_confirm_booking", [user.user_id, booking_id]))
    await notify_booking_change(booking)
    return ok(booking)


@router.patch("/bookings/{booking_id}/complete")
async def complete_booking(booking_id: int, user: AuthUser = Depends(require_auth)):
    booking = record_to_dict(await call_fn_one("fn_complete_booking", [user.user_id, booking_id]))
    await notify_booking_change(booking)
    return ok(booking)


@router.patch("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: int, body: CancelBody, user: AuthUser = Depends(require_auth)):
    result = await call_fn_jsonb("fn_cancel_booking", [user.user_id, booking_id, body.reason])
    await notify_booking_change(result)
    return ok(result)


@router.get("/bookings/mine")
async def my_bookings(user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)):
    rows = await call_fn("fn_list_bookings_for_resident", [user.user_id, pagination.limit, pagination.offset])
    total = int(rows[0]["total_count"]) if rows else 0
    items = [r["booking"] for r in rows]
    return ok(paginated_envelope(items, total, pagination))


@router.get("/bookings/provider")
async def provider_bookings(
    provider_id: int = Query(...), user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)
):
    rows = await call_fn("fn_list_bookings_for_provider", [user.user_id, provider_id, pagination.limit, pagination.offset])
    total = int(rows[0]["total_count"]) if rows else 0
    items = [r["booking"] for r in rows]
    return ok(paginated_envelope(items, total, pagination))


# Registered after the literal /bookings/mine and /bookings/provider routes above —
# a wildcard path param registered first would shadow them (Starlette matches by
# registration order, not specificity).
@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: int, user: AuthUser = Depends(require_auth)):
    return ok(await call_fn_jsonb("fn_get_booking_detail", [user.user_id, booking_id]))
