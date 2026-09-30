from datetime import datetime

from pydantic import BaseModel


class CreateNoticeBody(BaseModel):
    community_id: int
    title: str
    content: str
    priority: str = "normal"
    attachments: list = []
    audience_type: str = "all"
    audience_ref: dict = {}
    expiry_at: datetime | None = None
