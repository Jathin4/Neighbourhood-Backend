from pydantic import BaseModel, Field


class SubmitReviewBody(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str | None = None
    photo_url: str | None = None


class ResponseBody(BaseModel):
    response: str


class FlagBody(BaseModel):
    reason: str
