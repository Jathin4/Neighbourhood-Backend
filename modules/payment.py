import json

from fastapi import APIRouter, Depends, Request

from config import settings
from database.db import call_fn, call_fn_jsonb, call_fn_one, record_to_dict
from deps import AuthUser, require_auth
from envelope import ok
from idempotency import require_idempotency_key
from pagination import Pagination, pagination_params
from adapters.payment.razorpay_adapter import RazorpayAdapter
from models.payment_model import InitiatePaymentBody, OffPlatformBody

router = APIRouter()
gateway = RazorpayAdapter()


@router.post("/bookings/{booking_id}/payments/initiate")
async def initiate_payment(
    booking_id: int, body: InitiatePaymentBody, user: AuthUser = Depends(require_auth), idempotency_key: str = Depends(require_idempotency_key)
):
    payment = record_to_dict(await call_fn_one("fn_initiate_payment", [user.user_id, booking_id, body.amount_minor_units, idempotency_key]))

    checkout: dict
    try:
        order = await gateway.create_order(body.amount_minor_units, payment["currency"], str(payment["id"]))
        await call_fn_one("fn_attach_gateway_ref", [payment["id"], order.gateway_order_id])
        checkout = order.checkout_payload
    except Exception as exc:
        # Gateway not configured yet (no live keys) — payment row still exists as Pending;
        # the frontend can retry initiate once RAZORPAY_KEY_ID/SECRET are set.
        checkout = {"error": "gateway_not_configured", "message": str(exc)}

    return ok({"payment": payment, "checkout": checkout}, 201)


@router.post("/payments/webhook")
async def payment_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if settings.razorpay_webhook_secret:
        event = gateway.verify_and_parse_webhook(raw_body, signature)
        event_id, gateway_ref, status, amount = event.event_id, event.gateway_ref, event.status, event.amount_minor_units
    else:
        # Dev fallback: no webhook secret configured yet, trust the parsed body directly.
        parsed = json.loads(raw_body.decode("utf-8"))
        event_id, gateway_ref, status, amount = parsed.get("event_id"), parsed.get("gateway_ref"), parsed.get("status"), parsed.get("amount_minor_units")

    result = await call_fn_jsonb("fn_process_payment_webhook", [event_id, gateway_ref, status, amount])
    return ok(result)


@router.get("/providers/{provider_id}/ledger")
async def settlement_ledger(provider_id: int, user: AuthUser = Depends(require_auth), pagination: Pagination = Depends(pagination_params)):
    rows = await call_fn("fn_get_settlement_ledger", [user.user_id, provider_id, pagination.limit, pagination.offset])
    total = int(rows[0]["total_count"]) if rows else 0
    totals = {"gross": int(rows[0]["total_gross"]), "fee": int(rows[0]["total_fee"]), "net": int(rows[0]["total_net"])} if rows else {"gross": 0, "fee": 0, "net": 0}
    return ok({
        "items": [r["entry"] for r in rows],
        "total": total,
        "limit": pagination.limit,
        "offset": pagination.offset,
        "totals": totals,
    })


@router.post("/bookings/{booking_id}/off-platform-payment")
async def record_off_platform_payment(booking_id: int, body: OffPlatformBody, user: AuthUser = Depends(require_auth)):
    row = record_to_dict(await call_fn_one("fn_record_off_platform_payment", [user.user_id, booking_id, body.note]))
    return ok(row, 201)
