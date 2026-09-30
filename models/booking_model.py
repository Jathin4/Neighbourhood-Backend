from pydantic import BaseModel


class CreateBookingBody(BaseModel):
    provider_id: int
    category_id: int
    description: str
    preferred_time: str | None = None
    location: str | None = None
    attachments: list = []
    budget_minor: int | None = None


class RespondBody(BaseModel):
    action: str  # accept | reject | propose
    proposed_time: str | None = None
    note: str | None = None


class CancelBody(BaseModel):
    reason: str
