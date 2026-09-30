from pydantic import BaseModel


class CreateCategoryBody(BaseModel):
    name: str
    key: str
    icon: str | None = None
    commission_rate: float = 0.15
    sla_hours: int = 48


class UpdateCategoryBody(BaseModel):
    commission_rate: float | None = None
    sla_hours: int | None = None
    config: dict | None = None


class FeatureFlagBody(BaseModel):
    community_id: int | None = None
    key: str
    enabled: bool
    config: dict = {}
