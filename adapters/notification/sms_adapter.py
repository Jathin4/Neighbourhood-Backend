import httpx

from adapters.notification.base import SendResult
from config import settings


class SmsAdapter:
    """SMS adapter for the 99smsservice.com gateway (DLT-registered sender, used for OTP).
    All secrets come from env (.env, gitignored) — never hardcoded."""

    async def send(self, to: str, body: str, variables: dict[str, str] | None = None) -> SendResult:
        variables = variables or {}
        if not settings.sms_gateway_base_url or not settings.sms_api_key:
            # Local/dev fallback: log instead of calling out, so OTP flows still work without live SMS creds.
            print(f'[SmsAdapter:DEV] to={to} body="{body}"')
            return SendResult(delivered=True, provider_response={"simulated": True})

        message = body
        for key, value in variables.items():
            message = message.replace(f"{{{key}}}", value)

        params = {
            "action": "send-sms",
            "api_key": settings.sms_api_key,
            "to": to,
            "from": settings.sms_sender_id,
            "sms": message,
            "p_entity_id": settings.sms_entity_id,
            "temp_id": settings.sms_template_id,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(settings.sms_gateway_base_url, params=params)

        return SendResult(delivered=resp.status_code < 400, provider_response={"status": resp.status_code, "body": resp.text})
