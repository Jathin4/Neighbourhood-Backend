from datetime import datetime

from pydantic import BaseModel


class CreateCommunityBody(BaseModel):
    name: str
    city: str
    default_currency: str = "INR"


class UpdateCommunityBody(BaseModel):
    name: str
    city: str


class CreateTowerBody(BaseModel):
    community_id: int
    name: str


class CreateUnitBody(BaseModel):
    tower_id: int
    name: str


class BulkImportBody(BaseModel):
    rows: list[dict]  # [{phone, full_name, tower_name, unit_name, household_relationship}]


class MembershipDecisionBody(BaseModel):
    status: str  # Approved | Rejected
    reason: str | None = None


class VerificationBody(BaseModel):
    new_state: str  # Draft|Submitted|UnderReview|Verified|Rejected|Suspended
    reason: str | None = None
    verification_expiry_at: datetime | None = None


class CommitteeRoleBody(BaseModel):
    community_id: int
    target_user_id: int
    capabilities: list[str]


class AdminCreateProviderBody(BaseModel):
    phone: str
    business_name: str
    categories: list[str]
    community_id: int
    auto_verify: bool = True


class DecideCommunityRequestBody(BaseModel):
    new_status: str  # Approved|Rejected
    note: str | None = None


class CuratedProviderBody(BaseModel):
    community_id: int
    provider_id: int
    label: str = "preferred"


class ModerationBody(BaseModel):
    action: str  # hide | restore | delete
    reason: str | None = None
