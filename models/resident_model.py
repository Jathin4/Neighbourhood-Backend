from pydantic import BaseModel, Field


class RegisterBody(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    photo_url: str | None = None
    household_relationship: str | None = None
    language_preference: str = "en"


class PatchMeBody(BaseModel):
    full_name: str | None = None
    photo_url: str | None = None
    household_relationship: str | None = None
    language_preference: str | None = None


class MembershipRequestBody(BaseModel):
    community_id: int
    method: str  # invite | admin-approval | resident-data-match


class AccountStateBody(BaseModel):
    account_state: str
    reason: str | None = None


class PrivacyBody(BaseModel):
    phone_visible: bool | None = None
    email_visible: bool | None = None
