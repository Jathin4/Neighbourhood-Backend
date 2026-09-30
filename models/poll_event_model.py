from datetime import datetime

from pydantic import BaseModel


class PollOption(BaseModel):
    id: str
    label: str


class CreatePollBody(BaseModel):
    community_id: int
    question: str
    options: list[PollOption]
    type: str = "single"
    audience_type: str = "all"
    audience_ref: dict = {}
    is_anonymous: bool = False
    end_at: datetime


class VoteBody(BaseModel):
    option_ids: list[str]


class CreateEventBody(BaseModel):
    community_id: int
    title: str
    date_time: datetime
    location: str | None = None
    capacity: int | None = None
    description: str | None = None


class RsvpBody(BaseModel):
    status: str  # Going | NotGoing
