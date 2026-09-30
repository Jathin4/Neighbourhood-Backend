from app.adapters.notification.base import SendResult


class LoggingStubAdapter:
    """WhatsApp/Email — stubbed for MVP, same interface so swapping in Twilio/SES
    later is a one-line change in notification_module's adapter_for() (push
    already swapped to FcmPushAdapter, see push_adapter.py)."""

    def __init__(self, label: str):
        self.label = label

    async def send(self, to: str, body: str, variables: dict[str, str] | None = None) -> SendResult:
        print(f'[{self.label}:DEV] to={to} body="{body}"')
        return SendResult(delivered=True, provider_response={"simulated": True})


whatsapp_adapter = LoggingStubAdapter("WhatsAppAdapter")
email_adapter = LoggingStubAdapter("EmailAdapter")
