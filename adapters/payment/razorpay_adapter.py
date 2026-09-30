import base64
import hashlib
import hmac
import json
from dataclasses import dataclass

import httpx

from config import settings


@dataclass
class CreateOrderResult:
    gateway_order_id: str
    amount_minor_units: int
    currency: str
    checkout_payload: dict


@dataclass
class WebhookEvent:
    event_id: str
    gateway_ref: str
    status: str
    amount_minor_units: int | None
    raw: dict


class RazorpayAdapter:
    """India-compatible gateway adapter (Razorpay Orders API shape). Requires
    RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET / RAZORPAY_WEBHOOK_SECRET once real
    keys are available — until then this fails loudly rather than pretending
    to charge anyone."""

    async def create_order(self, amount_minor_units: int, currency: str, receipt: str, notes: dict | None = None) -> CreateOrderResult:
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise RuntimeError("RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET not configured")

        auth = base64.b64encode(f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}".encode()).decode()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.razorpay.com/v1/orders",
                headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
                json={"amount": amount_minor_units, "currency": currency, "receipt": receipt, "notes": notes or {}},
            )
        if resp.status_code >= 400:
            raise RuntimeError(f"Razorpay order creation failed: {resp.status_code} {resp.text}")

        order = resp.json()
        return CreateOrderResult(
            gateway_order_id=order["id"],
            amount_minor_units=order["amount"],
            currency=order["currency"],
            checkout_payload={"key": settings.razorpay_key_id, "order_id": order["id"], "amount": order["amount"], "currency": order["currency"]},
        )

    def verify_and_parse_webhook(self, raw_body: bytes, signature_header: str | None) -> WebhookEvent:
        if not signature_header or not settings.razorpay_webhook_secret:
            raise RuntimeError("Missing webhook signature or secret")

        expected = hmac.new(settings.razorpay_webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature_header):
            raise RuntimeError("Invalid webhook signature")

        payload = json.loads(raw_body.decode("utf-8"))
        entity = payload.get("payload", {}).get("payment", {}).get("entity") or payload.get("payload", {}).get("order", {}).get("entity") or {}
        return WebhookEvent(
            event_id=payload.get("id", entity.get("id")),
            gateway_ref=entity.get("order_id", entity.get("id")),
            status=_map_status(payload.get("event", "")),
            amount_minor_units=entity.get("amount"),
            raw=payload,
        )


def _map_status(event: str) -> str:
    if "captured" in event:
        return "captured"
    if "authorized" in event:
        return "authorized"
    if "failed" in event:
        return "failed"
    if "refunded" in event:
        return "refunded"
    return "paid"
