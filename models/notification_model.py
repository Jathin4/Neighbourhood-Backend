from pydantic import BaseModel


class PatchPreference(BaseModel):
    channel: str
    category: str
    enabled: bool
