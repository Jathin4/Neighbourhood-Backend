from pydantic import BaseModel


class SubmitApplicationBody(BaseModel):
    business_name: str
    categories: list[str]
    service_area: dict = {}
    operating_hours: dict = {}
    pricing_model: dict = {}


class SubmitDocumentBody(BaseModel):
    doc_type: str
    file_url: str


class RequestServeCommunityBody(BaseModel):
    community_id: int


class UpdateProfileBody(BaseModel):
    business_name: str | None = None
    categories: list[str] | None = None
    operating_hours: dict | None = None
    pricing_model: dict | None = None
    service_area: dict | None = None


class ServiceCatalogueBody(BaseModel):
    pricing_model: dict


class AddStaffBody(BaseModel):
    staff_phone: str
    role: str = "technician"
    name: str | None = None


class UpdateStaffBody(BaseModel):
    role: str | None = None
    active: bool | None = None


class AvailabilityBody(BaseModel):
    weekly_schedule: dict | None = None
    blackout_dates: list | None = None


class SupportTicketBody(BaseModel):
    provider_id: int | None = None
    subject: str
    description: str


class TicketMessageBody(BaseModel):
    message: str
