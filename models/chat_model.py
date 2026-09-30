from pydantic import BaseModel, Field


class StartConversationBody(BaseModel):
    other_user_id: int


class SendMessageBody(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
