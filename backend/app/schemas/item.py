import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    model_config = ConfigDict(extra="ignore")


class ItemUpdate(ItemBase):
    title: str | None = None


class ItemPublic(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(BaseModel):
    data: list[ItemPublic]
    count: int