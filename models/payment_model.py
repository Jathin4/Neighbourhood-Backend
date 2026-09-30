from pydantic import BaseModel, Field


class InitiatePaymentBody(BaseModel):
    amount_minor_units: int = Field(gt=0)


class OffPlatformBody(BaseModel):
    note: str
