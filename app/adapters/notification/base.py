from dataclasses import dataclass
from typing import Protocol


@dataclass
class SendResult:
    delivered: bool
    provider_response: dict


class NotificationAdapter(Protocol):
    async def send(self, to: str, body: str, variables: dict[str, str] | None = None) -> SendResult: ...
