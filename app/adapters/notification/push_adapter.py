from app.adapters.notification.base import SendResult
from app.firebase.client import send_push


class FcmPushAdapter:
    """Adapts app.firebase.client.send_push to the NotificationAdapter interface —
    all Firebase-specific code stays in app/firebase/, this is just the plug."""

    async def send(self, to: str, body: str, variables: dict[str, str] | None = None) -> SendResult:
        title = (variables or {}).get("title") or "Trusted Neighbourhood Network"
        delivered = await send_push(to, title, body)
        return SendResult(delivered=delivered, provider_response={"fcm": True})


push_adapter = FcmPushAdapter()
