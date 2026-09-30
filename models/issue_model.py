from pydantic import BaseModel


class CreateIssueBody(BaseModel):
    community_id: int
    category: str
    description: str
    media: list = []
    location: str | None = None
    urgency: str = "Normal"


class CommentBody(BaseModel):
    comment: str


class ReopenBody(BaseModel):
    reason: str


class AssignBody(BaseModel):
    owner_id: int
    note: str | None = None


class StatusBody(BaseModel):
    status: str
    note: str | None = None
