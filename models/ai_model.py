from pydantic import BaseModel


class AssistantQueryBody(BaseModel):
    query: str
